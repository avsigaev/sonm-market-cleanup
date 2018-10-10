import datetime
import json
import platform
import subprocess
import time


def log(s):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + s)


def set_sonmcli():
    if platform.system() == "Darwin":
        return "sonmcli_darwin_x86_64"
    else:
        return "sonmcli"


class Cli:
    def __init__(self, cli_):
        self.cli = cli_

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

