import json
import platform
import subprocess
import time

from urllib import request


class Cli:
    def __init__(self, path=None):
        if path:
            self.cli = path
        elif platform.system() == "Darwin":
            self.cli = "sonmcli_darwin_x86_64"
        else:
            self.cli = "sonmcli"

    def exec(self, param, retry=False, attempts=3, sleep_time=1):
        command = [self.cli] + param
        command.append("--json")
        attempt = 1
        # errors_ = []
        code_ = 0
        while True:
            result = subprocess.run(command, stdout=subprocess.PIPE)
            if result.returncode == 0:
                break
            if not retry or attempt > attempts:
                break
            # errors_.append(str(result.stdout))
            attempt += 1
            time.sleep(sleep_time)
        if result.returncode != 0:
            # log("Failed to execute command: " + ' '.join(command))
            # log('\n'.join(errors_))
            code_ = 1
            return code_, json.loads(result.stdout.decode("utf-8"))
        if result.stdout.decode("utf-8") == "null":
            code_ = 1
            return code_, json.loads(result.stdout.decode("utf-8"))
        return code_, json.loads(result.stdout.decode("utf-8"))


class DWH:
    def __init__(self, addr='https://dwh.livenet.sonm.com:15022'):
        self._server = addr
        self._headers = {'content-type': 'application/json'}

    def get_orders(self, params: dict) -> dict:
        data = json.dumps(params).encode('utf8')
        url = self._server + '/DWHServer/GetOrders/'
        req = request.Request(url, data=data, headers=self._headers)

        with request.urlopen(req) as resp:
            return json.loads(resp.read())
