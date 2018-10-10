#!/usr/bin/env python3

import threading
import subprocess
import json
import time

from cli import set_sonmcli, Cli, log


def get_orders():
    cmd_ = CURL + " '{\"type\": 2,\"status\": 2, \"counterpartyID\": [\"0x0000000000000000000000000000000000000000\"]}'"
    result = subprocess.run(cmd_, shell=True, stdout=subprocess.PIPE)
    orders_ = json.loads(result.stdout)
    suppliers_raw_ = []
    for i in orders_["orders"]:
        suppliers_raw_.append(i["order"]["authorID"])
    # log("List of suppliers on the market (with active orders):")
    suppliers = list(set(suppliers_raw_))
    # for s in suppliers:
    #     print(s)
    print("Total active ASK orders: " + str(len(orders_["orders"])))
    print("Total suppliers: " + str(len(suppliers)))

    return suppliers


def check_supplier(address):  # check if supplier is available; if not - add to the list for cleanup
    worker_address_ = "--worker-address=" + address
    status = SONM_CLI.exec(["worker", "status", worker_address_, "--timeout=1m"])
    if status[0] == 0:
        print("[OK] Worker " + address + " is a good boy, passing by.")
    elif str(status[1]["message"]).find("Unauthenticated") > 0:
        print("[OK] Worker " + address + " is a good boy (BUT has older SONM version), passing by.")
    elif str(status[1]["message"]).find("DeadlineExceeded") > 0:
        print("[GOTCHA] Worker " + address + " is offline, adding to the list for order removal")
        BAD_SUPPLIERS.append(address)
    elif status[0] == 1:
        print("[ERR] Unknown error: " + str(status[1]["message"]))
    return()


def get_orders_for_bad_suppliers(supplier):  # get ASK orders for unavailable supplier for clean
    command_ = CURL + " '{\"type\": 2,\"status\": 2, \"authorID\": \"" + supplier + "\"}'"
    result = subprocess.run(command_, shell=True, stdout=subprocess.PIPE)
    orders_ = json.loads(result.stdout)
    for i in orders_["orders"]:
        ORDERS_FOR_REMOVAL.append(i["order"]["id"])
    return None


def open_deal(order):  # quick-buy orders and close deals immediately; use threads
    print("Trying to buy order " + order)
    status = SONM_CLI.exec(["deal", "quick-buy", order, "--force", "--timeout=30s"])
    deal = "0"
    if status[0] == 0:
        print("[WTF] Expected timeout error, received deal ID: " + str(status[1]["deal"]["id"]))

    order_status = SONM_CLI.exec(["order", "status", order, "--timeout=30s"], retry=True)
    if order_status[0] == 0 and order_status[1]["dealID"] != "0":
        deal = order_status[1]["dealID"]
        print("Deal for order " + order + " is " + deal)
    elif order_status[0] == 0:
        print("Could not open deal for order " + order)
    elif order_status[0] == 1:
        print("Could not get status for order " + order)

    close_deal(deal)

    return()


def close_deal(deal):
    print("Closing deal: " + deal + "...")
    if deal != "0":
        status = SONM_CLI.exec(["deal", "close", deal], retry=True)
        if status[0] == 0:
            print("Deal " + deal + " closed.")
        else:
            print("ERROR while closing deal: " + deal)
    DEALS.append(deal)


def calc_expanses():
    total_spendings_ = 0.0
    for deal in DEALS:
        status = SONM_CLI.exec(["deal", "status", deal], retry=True)
        if status[0] == 0:
            cost = float(status[1]["deal"]["totalPayout"])/1e18
            print("Deal " + deal + " cost = " + str(cost) + " SNM")
            total_spendings_ += cost
    return total_spendings_


def main():
    global SONM_CLI
    SONM_CLI = Cli(set_sonmcli())
    global BAD_SUPPLIERS
    BAD_SUPPLIERS = []
    global CURL
    CURL = "curl -s https://dwh.livenet.sonm.com:15022/DWHServer/GetOrders/ -d"
    global ORDERS_FOR_REMOVAL
    ORDERS_FOR_REMOVAL = []
    global DEALS
    DEALS = []

    suppliers = get_orders()

    print("========= Checking worker status ==========")
    for address in suppliers:
        threading.Thread(target=check_supplier, kwargs={'address': address}).start()
        time.sleep(1)
    time.sleep(80)

    print("=========== Bad guys (" + str(len(BAD_SUPPLIERS)) + ") are: ===========")
    for i in BAD_SUPPLIERS:
        print(i)

    print("====== Gathering orders for removal ======")
    for address in BAD_SUPPLIERS:
        threading.Thread(target=get_orders_for_bad_suppliers, kwargs={'supplier': address}).start()
    time.sleep(3)

    print("TOTAL Orders for removal: " + str(len(ORDERS_FOR_REMOVAL)))

    print("======== Removing orders... ========")
    for order in ORDERS_FOR_REMOVAL:
        threading.Thread(target=open_deal, kwargs={'order': order}).start()
        time.sleep(1)

    while True:
        if len(DEALS) == len(ORDERS_FOR_REMOVAL):
            break
    total_spendings = calc_expanses()
    print("=====================" + "\n" + "Total spendings: " + str(total_spendings) + " SNM")


if __name__ == "__main__":
    main()
