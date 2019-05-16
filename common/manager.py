import threading
import logging
import re
import time
import json
import os
from ping3 import ping
import configparser
import requests
import hashlib
from time import sleep
from common.file_download import UPDATEdownload


def GetFileMd5(filename):
    if not os.path.isfile(filename):
        return None
    myHash = hashlib.md5()
    f = open(filename, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myHash.update(b)
    f.close()
    return myHash.hexdigest().upper()

class UPDATEManager(threading.Thread):
    def __init__(self, stream_pub):
        threading.Thread.__init__(self)
        self._thread_stop = False
        self._mqtt_stream_pub = stream_pub
        self._download = None
        self._new_version_md5 = None

    def check_version(self):
        new_version = None
        new_version_md5 = None
        new_version_url = 'https://thingscloud.oss-cn-beijing.aliyuncs.com/download/Vnet/version.json'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
        version = None
        with open("./version.json", 'r') as load_f:
            version = json.load(load_f)['version']
        response = requests.get(new_version_url, headers=headers)
        if response:
            ret = json.loads(response.content.decode("utf-8"))
            new_version = ret['version']
            new_version_md5 = ret['md5']
            self._new_version_md5 = new_version_md5
        if int(new_version) > int(version):
            return {"new_version": new_version, "version": version, "update": True}
        else:
            return {"new_version": new_version, "new_version_md5": new_version_md5, "version": version, "update": False}

    def on_update(self, update_url, save_file):
        if not self._download.is_download():
            self._download.start_download(update_url, save_file)
        return {"status": "upgrading"}

    def check_update_status(self):
        if self._download.is_download():
            return {"status": "upgrading"}
        else:
            filemd5 = GetFileMd5('./_update/freeioe_Rprogramming.zip')
            if filemd5 and self._new_version_md5 == filemd5:
                curpath = os.getcwd()
                workdir = curpath
                cmd1 = curpath + '\\_update\\_update.exe'
                from helper.process_runner import Process_Runner
                runner = Process_Runner(workdir, cmd1)
                runner.run()
                return {"status": "done", "md5": filemd5}
            else:
                return {"status": "failed", "md5": None}

    def check_servers_list(self):
        servers_list = None
        result = []
        with open("./servers_list.json", 'r') as load_f:
            servers_list = json.load(load_f)
        if servers_list:
            for k, v in servers_list.items():
                ret = ping(v, unit='ms', timeout=1)
                if ret:
                    result.append({"desc": k, "host": v, "delay": str(int(ret))+'ms'})
                pass
        return result

    def on_event(self, event, ul_value):
        return True

    def start(self):
        self._download = UPDATEdownload(self)
        self._download.start()
        threading.Thread.start(self)

    def run(self):
        while not self._thread_stop:
            time.sleep(1)
        logging.warning("Close UPDATE!")

    def stop(self):
        self._download.stop()
        self._thread_stop = True
        self.join()
