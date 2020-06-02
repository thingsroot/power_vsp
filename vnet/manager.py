import threading
import logging
import vnet
import re
import time
import json
import os
import wmi
import pythoncom
import winreg
import platform
import configparser
import requests
import hashlib
from requests.auth import HTTPBasicAuth
from time import sleep
from vnet.route_fix import VNETRouterFix
from ping3 import ping

default_frpc = {
    "admin_addr": "127.0.0.1",
    "admin_port": "7413",
    "login_fail_exit": "false",
    "server_addr": "thingsroot.com",
    "server_port": "1699",
    "token": "F^AYnHp29U=M96#o&ESqXB3pL=$)W*qr",
    "protocol": "kcp"
}

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
    return myHash.hexdigest()

class VNETManager(threading.Thread):
    def __init__(self, stream_pub):
        threading.Thread.__init__(self)
        self._services = ["frpc_Vnet_service", "tinc.tofreeioebridge", "tinc.tofreeioerouter"]
        self._working_config = {}
        self._working_proxyname = None
        self._result = {}
        self._handlers = []
        self._timeout = 5
        self._thread_stop = False
        self._mqtt_stream_pub = stream_pub
        self._enable_heartbeat = True
        self._heartbeat_timeout = time.time() + 90
        self._route_fix = None
        self._download = None
        self._AuthorizationCode = None

    def wmi_in_thread(self, myfunc, *args, **kwargs):
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            return myfunc(c, *args, **kwargs)
        finally:
            pythoncom.CoUninitialize()

    def env_check(self, wmis):
        check_env_ret = {}
        TAP_Nics = wmis.Win32_NetworkAdapter(Manufacturer="TAP-Windows Provider V9")
        if len(TAP_Nics) > 0:
            check_env_ret["tap_nic"] = None
            for tap_nic in TAP_Nics:
                # print(tap_nic.NetConnectionID)
                if tap_nic.NetConnectionID == "symbridge":
                    check_env_ret["tap_nic"] = tap_nic.NetConnectionID
                    break
            if not check_env_ret["tap_nic"]:
                # print(TAP_Nics[0].NetConnectionID)
                check_env_ret["tap_nic"] = TAP_Nics[0].NetConnectionID
        else:
            check_env_ret["tap_nic"] = False
        # print('frpc::', os.access("vnet/tinc/_frpc/frpc.exe", os.F_OK))
        # print('tincd:::', os.access("vnet/tinc/tincd.exe", os.F_OK))
        if os.access("vnet/tinc/_frpc/frpc.exe", os.F_OK):
            check_env_ret["frpc_bin"] = True
        else:
            check_env_ret["frpc_bin"] = False
        cmd = 'sc qc frpc_Vnet_service|find /I "BINARY_PATH_NAME"'
        cmd_ret = os.popen(cmd).read().strip()
        if os.path.abspath('.') in cmd_ret:
            check_env_ret["frpc_Vnet_service"] = True
        else:
            check_env_ret["frpc_Vnet_service"] = False
        if os.access("vnet/tinc/tincd.exe", os.F_OK):
            check_env_ret["tinc_bin"] = True
        else:
            check_env_ret["tinc_bin"] = False
        cmd = 'sc qc tinc.tofreeioerouter|find /I "BINARY_PATH_NAME"'
        cmd_ret = os.popen(cmd).read().strip()
        if os.path.abspath('.') in cmd_ret:
            check_env_ret["tinc.tofreeioerouter"] = True
        else:
            check_env_ret["tinc.tofreeioerouter"] = False
        cmd = 'sc qc tinc.tofreeioebridge|find /I "BINARY_PATH_NAME"'
        cmd_ret = os.popen(cmd).read().strip()
        if os.path.abspath('.') in cmd_ret:
            check_env_ret["tinc.tofreeioebridge"] = True
        else:
            check_env_ret["tinc.tofreeioebridge"] = False
        return check_env_ret

    def env_fix(self):
        _local_env = self.wmi_in_thread(self.env_check)
        curpath = os.getcwd()
        if not _local_env["frpc_Vnet_service"]:
            cmd1 = curpath + '\\vnet\\tinc\\_install_service.cmd'
            # print('service::', os.access(curpath + '\\vnet\\tinc\\_install_service.cmd', os.F_OK))
            workdir = curpath
            from helper.process_runner import Process_Runner
            runner = Process_Runner(workdir, cmd1)
            runner.run()
        if not _local_env["tap_nic"]:
            if "XP" in platform.platform():
                pass
            else:
                if os.access(curpath + '\\vnet\\tinc\\tap-win\\tap-windows.exe', os.F_OK):
                    cmd2 = '"' + curpath + '\\vnet\\tinc\\tap-win\\tap-windows.exe' + '"' + ' /S'
                    cmd_ret = os.popen(cmd2)
                else:
                    logging.info('tap-windows.exe is nonexistent')
        # sleep(3)
        # _local_env = wmi_in_thread(check_local_env)
        # for k, v in _local_env.items():
        #     print(k, v)
        #     if not v:
        #         return {"message": False}
        return {"action": True}

    def list_taps(self, wmis):
        tap_nics = []
        TAP_Nics = wmis.Win32_NetworkAdapter(Manufacturer="TAP-Windows Provider V9")
        if len(TAP_Nics) > 0:
            for tap_nic in TAP_Nics:
                tap_nics.append(tap_nic.NetConnectionID)
        else:
            logging.info('NO TAP-Windows!')
        return tap_nics

    def prepend_tap(self, wmiService):
        if self._working_config:
            dAdapter = "symbridge"
            net_mode = self._working_config["vnet_cfg"]["net_mode"]
            vpn_ip = self._working_config["vnet_cfg"]["tap_ip"]
            vpn_netmask = self._working_config["vnet_cfg"]["tap_netmask"]
            ipaddr = [vpn_ip]
            subnet = [vpn_netmask]
            if net_mode == "router":
                dAdapter = "symrouter"
                ipaddr = ["10.222.0.2"]
                subnet = ["255.255.255.0"]
            destnic = None
            TAP_Windows_Nics = wmiService.Win32_NetworkAdapter(Manufacturer="TAP-Windows Provider V9")
            if len(TAP_Windows_Nics) > 0:
                for tap_nic in TAP_Windows_Nics:
                    if tap_nic.NetConnectionID == "symbridge":
                        tap_nic.disable
                        sleep(0.5)
                        tap_nic.enable
                        destnic = tap_nic.GUID
                        # print(tap_nic.Manufacturer)
                        # print(tap_nic.GUID)
                        # print(tap_nic.NetConnectionID)
                        # print(tap_nic.NetEnabled)
                        # print(tap_nic.ServiceName)
                        # print(tap_nic.ProductName)
                        break
                if not destnic:
                    TAP_Windows_Nics[0].NetConnectionID = dAdapter
                    TAP_Windows_Nics[0].disable
                    sleep(1)
                    TAP_Windows_Nics[0].enable
                    destnic = TAP_Windows_Nics[0].GUID
            else:
                logging.info('NO TAP-Windows!')
            if destnic:
                colNicConfigs = wmiService.Win32_NetworkAdapterConfiguration(
                    IPEnabled=False, ServiceName="tap0901", SettingID=destnic)
                if len(colNicConfigs) < 1:
                    self._result["tap_nic"] = None
                    return False
                else:
                    Adapter1 = colNicConfigs[0]
                    RetVal = Adapter1.EnableStatic(ipaddr, subnet)
                    if RetVal:
                        self._result["tap_nic"] = destnic
                    return True
            else:
                return False

    def wirte_common_frpcini(self, file, vnet_cfg=None, frps_cfg=None):
        if os.access(file, os.F_OK):
            os.remove(file)
        self._working_config['vnet_cfg'] = vnet_cfg
        if not frps_cfg:
            frps_cfg = default_frpc
        else:
            if frps_cfg.get('server_addr'):
                default_frpc['server_addr'] = frps_cfg['server_addr']
            else:
                default_frpc['server_addr'] = "bj.proxy.thingsroot.com"
            if frps_cfg.get('server_port'):
                default_frpc['server_port'] = frps_cfg['server_port']
            else:
                default_frpc['server_port'] = "1699"
            if frps_cfg.get('token'):
                default_frpc['token'] = frps_cfg['token']
            else:
                default_frpc['token'] = "F^AYnHp29U=M96#o&ESqXB3pL=$)W*qr"
            frps_cfg = default_frpc
        frps_cfg['protocol'] = self._working_config['vnet_cfg']['net_protocol']
        # print(frps_cfg)
        inicfg = configparser.ConfigParser()
        inicfg.read(file)
        sections = inicfg.sections()
        if "common" not in sections:
            inicfg.add_section("common")
        for k, v in frps_cfg.items():
            inicfg.set("common", k, v)
        inicfg.write(open(file, 'w'))
        self._working_config['common'] = frps_cfg
        return True

    def add_proxycfg_frpcini(self, file, proxycfg):
        inicfg = configparser.ConfigParser()
        inicfg.read(file)
        for k, v in proxycfg.items():
            self._working_proxyname = k
            inicfg.add_section(k)
            for mk, mv in v.items():
                inicfg.set(k, mk, mv)
        inicfg.write(open(file, 'w'))
        self._working_config['proxy'] = proxycfg
        return True

    def read_frpcini(self, file):
        frpc = {}
        if os.access(file, os.F_OK):
            inicfg = configparser.ConfigParser()
            inicfg.read(file)
            sections = inicfg.sections()
            for s in sections:
                items = inicfg.items(s)
                d = {}
                for p, q in items:
                    d[p] = q
                frpc[s] = d
        return frpc

    def delete_frpcini(self, file):
        if os.access(file, os.F_OK):
            os.remove(file)
            if os.access(file, os.F_OK):
                return False
            else:
                return True
        else:
            return True

    def check_binpath(self):
        rRoot = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        subDir = r'Software\tinc'
        tincbinpath = os.getcwd() + r"\vnet\tinc"
        tincinscmd = ['sc stop tinc.tofreeioebridge', 'sc delete tinc.tofreeioebridge',
                      'sc stop tinc.tofreeioerouter', 'sc delete tinc.tofreeioerouter',
                      tincbinpath + r'\tincd.exe -n ' + 'tofreeioebridge', 'sc stop tinc.tofreeioebridge',
                      tincbinpath + r'\tincd.exe -n ' + 'tofreeioerouter', 'sc stop tinc.tofreeioerouter',
                      'sc config tinc.tofreeioebridge start= demand',
                      'sc config tinc.tofreeioerouter start= demand']
        keyHandle = None
        try:
            keyHandle = winreg.OpenKey(rRoot, subDir)
        except Exception as ex:
            logging.error(subDir + " 不存在")
            logging.error(ex)
        if not keyHandle:
            keyHandle = winreg.CreateKey(rRoot, subDir)
        if keyHandle:
            count = winreg.QueryInfoKey(keyHandle)[1]  # 获取该目录下所有键的个数(0-下属键个数;1-当前键值个数)
            if not count:
                logging.error.info("创建 tinc path:: {0}".format(tincbinpath))
                winreg.SetValue(rRoot, subDir, winreg.REG_SZ, tincbinpath)
                for cmd in tincinscmd:
                    os.popen(cmd)
                    time.sleep(0.01)
            else:
                name, key_value, value_type = winreg.EnumValue(keyHandle, 0)
                if tincbinpath not in key_value:
                    logging.error.info("修改 tinc path:: {0}".format(tincbinpath))
                    winreg.SetValue(rRoot, subDir, winreg.REG_SZ, tincbinpath)
                    for cmd in tincinscmd:
                        os.popen(cmd)
                        time.sleep(0.01)

    def service_status(self):
        services_status = {}
        is_running = None
        for s in self._services:
            cmd1 = 'sc query ' + s + '|find /I "STATE"'
            cmd_ret = os.popen(cmd1).read().strip()
            cmd_ret = re.split('\s+', cmd_ret)
            if len(cmd_ret) > 1:
                services_status[s] = cmd_ret[3]
            pass
        for val in services_status.values():
            if val == "RUNNING":
                is_running = True
                break
            else:
                is_running = False
        services_status['is_running'] = is_running
        self._working_config['is_running'] = is_running
        if not self._working_config.get('vnet_cfg'):
            if is_running:
                logging.warning('stopping services!')
                for s in self._services:
                    cmd1 = 'sc stop ' + s
                    os.popen(cmd1)
        return services_status

    def service_start(self, vnettype, proxytype="frpc"):
        proxyService = "frpc_Vnet_service"
        if proxytype == "npc":
            proxyService = "Npc"
        dest_services = [proxyService, "tinc.tofreeioebridge"]
        if vnettype == 'router':
            dest_services = [proxyService, "tinc.tofreeioerouter"]
        services_start = 0
        self.check_binpath()
        for s in dest_services:
            cmd1 = 'sc start ' + s + '|find /I "STATE"'
            cmd_ret = os.popen(cmd1).read().strip()
            # print('sc resut:', cmd_ret)
            sleep(0.1)
            if cmd_ret:
                logging.info(s + ' is starting!')
                services_start = services_start + 1
        if services_start == len(dest_services):
            self._result["services_start"] = True
            self._working_config['is_running'] = True
        else:
            self._result["services_start"] = False
        # os.remove(os.getcwd() + '\\vnet\\tinc\\_frpc\\frpc.ini')
        action_result = {}
        action_result['tap_nic'] = self._result["tap_nic"]
        action_result['services_start'] = self._result["services_start"]
        return action_result

    def service_stop(self, vnettype, proxytype="frpc"):
        proxyService = "frpc_Vnet_service"
        if proxytype == "npc":
            proxyService = "Npc"
        dest_services = [proxyService, "tinc.tofreeioebridge"]
        if vnettype == 'router':
            dest_services = [proxyService, "tinc.tofreeioerouter"]
        services_start = 0
        for s in dest_services:
            cmd1 = 'sc stop ' + s + '|find /I "STATE"'
            cmd_ret = os.popen(cmd1).read().strip()
            # print('sc resut:', cmd_ret)
            sleep(0.1)
            if cmd_ret:
                logging.info(s + ' is stopping!')
                services_start = services_start + 1
        if services_start == len(dest_services):
            self._result["services_stop"] = True
            self._working_config['is_running'] = False

        else:
            self._result["services_stop"] = False
        if os.access(os.getcwd() + '\\vnet\\tinc\\_frpc\\frpc.ini', os.F_OK):
            os.remove(os.getcwd() + '\\vnet\\tinc\\_frpc\\frpc.ini')
        action_result = {}
        action_result['services_stop'] = self._result["services_stop"]
        return action_result

    def local_proxy_status(self):
        proxy = None
        if self._working_config.get('is_running'):
            url = 'http://127.0.0.1:7413/api/status'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
            proxies = {}
            try:
                response = requests.get(url, headers=headers)
                ret_content = json.loads(response.content.decode("utf-8"))
                proxies = ret_content['tcp']
                proxy_key = self._working_proxyname
                for pr in proxies:
                    if pr['name'] == proxy_key:
                        proxy = pr
                        break
            except Exception as ex:
                logging.error('local_proxy_status :: ' + str(ex))
        return proxy

    def cloud_proxy_status(self, url=None, auth=None):
        proxy = None
        if self._working_config.get('is_running'):
            if not url:
                url = 'http://' + self._working_config["vnet_cfg"]["node"] + ':2699/api/proxy/tcp'
            if not auth:
                auth = ('thingsrootadmin', 'Pa88word')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
            }
            proxies = {}
            try:
                response = requests.get(url, headers=headers, auth=HTTPBasicAuth(auth[0], auth[1]))
                ret_content = json.loads(response.content.decode("utf-8"))
                proxies = ret_content['proxies']
                proxy_key = self._working_proxyname
                for pr in proxies:
                    if pr['name'] == proxy_key:
                        proxy = pr
                        break
            except Exception as ex:
                logging.error('cloud_proxy_status :: ' + str(ex))
        return proxy

    def Handle_route_table(self):
        if self._working_config.get('is_running'):
            if self._working_config["vnet_cfg"]["net_mode"] == "router":
                if self._route_fix.is_fixing():
                    return
                remote_subnet = self._working_config["vnet_cfg"]["tap_ip"]
                remote_netmask = self._working_config["vnet_cfg"]["tap_netmask"]
                dest_ip = self._working_config["vnet_cfg"]["dest_ip"]
                self._route_fix.start_fix(remote_subnet, remote_netmask, dest_ip)

    def action_send_output(self, ioeurl, Authcode, send_data):
        url = ioeurl + '/api/method/iot.device_api.send_output'
        headers = {'AuthorizationCode': Authcode, 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(send_data))
        ret_content = None
        if response:
            ret_content = json.loads(response.content.decode("utf-8"))
        return ret_content

    def get_action_result(self, ioeurl, Authcode, id):
        url = ioeurl + '/api/method/iot.device_api.get_action_result?id=' + id
        headers = {'AuthorizationCode': Authcode, 'Accept': 'application/json'}
        response = requests.get(url, headers=headers)
        ret_content = None
        if response:
            ret_content = json.loads(response.content.decode("utf-8"))
        return ret_content

    def post_to_cloud(self, auth_code, output, peer_host, peer_port):
        gate_sn = self._working_config['vnet_cfg'].get("gate_sn")
        rand_id = gate_sn + '/send_output/' + output + '/' + str(time.time())
        net_mode = self._working_config['vnet_cfg'].get("net_mode")
        user_id = self._working_config['vnet_cfg'].get("user_id")
        url = 'http://ioe.thingsroot.com'
        self._AuthorizationCode = auth_code
        vnet_config = {"net": net_mode, "Address": peer_host, "Port": peer_port, "proxy_name": self._working_proxyname, "user_id": user_id}
        datas = {
            "id": rand_id,
            "device": gate_sn,
            "data": {
                "device": gate_sn + ".freeioe_Vnet",
                "output": output,
                "value": vnet_config,
                "prop": "value"
            }
        }
        send_ret = self.action_send_output(url, self._AuthorizationCode, datas)
        # print("***********************", send_ret)
        if send_ret:
            action_ret = None
            self._result["cloud_mes"] = send_ret
            if send_ret['message'] == rand_id:
                for i in range(4):
                    action_ret = self.get_action_result(
                        url,  self._AuthorizationCode, rand_id)
                    if action_ret:
                        break
                    sleep(i + 1)
            # print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&", action_ret)
            if action_ret:
                self._result["gate_mes"] = action_ret["message"]
            else:
                if self._working_config.get('is_running'):
                    self.clean_all()
                self._result["gate_mes"] = 'gate has no response !'
                logging.info('gate has no response !')
            action_result = {}
            action_result['cloud_mes'] = self._result["cloud_mes"]
            action_result['gate_mes'] = self._result["gate_mes"]
            return action_result
        else:
            working_config = self._working_config
            if working_config.get('vnet_cfg'):
                self.clean_all()
            logging.info('cloud has no response !')
            return False

    def check_ip_alive(self, dest_ip):
        ret = ping(dest_ip, unit='ms', timeout=2)
        if ret:
            return {'message': 'online', "delay": str(int(ret)) + 'ms'}
        else:
            if self._working_config["vnet_cfg"]["net_mode"] == 'router':
                # print(self._working_config["vnet_cfg"]["net_mode"])
                self.Handle_route_table()
            return {'message': 'offline', "delay": 'timeout'}

    def enable_heartbeat(self, flag, timeout,  auth_code, gate_sn):
        # logging.error(flag, timeout,  auth_code, gate_sn)
        working_config = self._working_config
        if working_config.get('vnet_cfg'):
            if gate_sn == working_config['vnet_cfg']['gate_sn']:
                self._enable_heartbeat = flag
                self._heartbeat_timeout = int(timeout) + time.time()
                self.keep_vnet_alive(auth_code, gate_sn)
                return {"enable_heartbeat": self._enable_heartbeat, "heartbeat_timeout": self._heartbeat_timeout, "gate_sn": gate_sn}
            else:
                return False
        else:
            return False

    def keep_vnet_alive(self,  auth_code, gate_sn):
        if gate_sn and auth_code:
            rand_id = gate_sn + '/send_output/heartbeat_timeout/' + str(time.time())
            url = 'http://ioe.thingsroot.com'
            datas = {
                "id": rand_id,
                "device": gate_sn,
                "data": {
                    "device": gate_sn + ".freeioe_Vnet",
                    "output": 'heartbeat_timeout',
                    "value": 60,
                    "prop": "value"
                }
            }
            ret = self.action_send_output(url, auth_code, datas)


    def on_event(self, event, ul_value):
        return True

    def start(self):
        self._route_fix = VNETRouterFix(self)
        self._route_fix.start()
        # self._download = VNETdownload(self)
        # self._download.start()
        threading.Thread.start(self)

    def run(self):
        span = 0
        while not self._thread_stop:
            time.sleep(1)
            # print("_working_config::::", self._working_config)
            try:
                status = self.service_status()
                self._mqtt_stream_pub.vnet_status('SERVICES', json.dumps(status))
                self._mqtt_stream_pub.vnet_status('CONFIG', json.dumps(self._working_config))

                # print("xxxxxxx", self._working_config.get('is_running'), self._working_config.get('vnet_cfg'))
                if self._working_config.get('is_running') and self._working_config.get('vnet_cfg'):
                    if self._working_config["vnet_cfg"]["dest_ip"]:
                        data = self.check_ip_alive(self._working_config["vnet_cfg"]["dest_ip"])
                        self._mqtt_stream_pub.dest_status(self._working_config["vnet_cfg"]["dest_ip"], json.dumps(data))

                    local_proxy_status = self.local_proxy_status()
                    if local_proxy_status:
                        self._mqtt_stream_pub.proxy_status('LOCAL_PROXY', json.dumps(local_proxy_status))
                    else:
                        self._mqtt_stream_pub.proxy_status('LOCAL_PROXY', json.dumps({"status": "error"}))

                    if span == self._timeout:
                        cloud_proxy_status = self.cloud_proxy_status()
                        if cloud_proxy_status:
                            self._mqtt_stream_pub.proxy_status('CLOUD_PROXY', json.dumps(cloud_proxy_status))
                        else:
                            self._mqtt_stream_pub.proxy_status('CLOUD_PROXY', json.dumps({"status": "error"}))

                        span = span - 1
                    elif span == 0:
                        span = self._timeout
                    else:
                        span = span - 1

                if self._enable_heartbeat and time.time() > self._heartbeat_timeout:
                    if self._working_config.get('is_running'):
                        logging.warning('heartbeat timeout!')
                        self.clean_all()
                else:
                    # print(time.time() - self._heartbeat_timeout)
                    pass
            except Exception as ex:
                logging.warning('err!err!err!err!')
                logging.exception(ex)

        logging.warning("Close VNET!")

    def stop(self):
        self._route_fix.stop()
        # self._download.stop()
        self._thread_stop = True
        self.join()

    def clean_all(self):
        dest_services = ["frpc_Vnet_service", "tinc.tofreeioebridge", "tinc.tofreeioerouter"]
        services_start = 0
        for s in dest_services:
            cmd1 = 'sc stop ' + s + '|find /I "STATE"'
            cmd_ret = os.popen(cmd1).read().strip()
            # print('sc resut:', cmd_ret)
            sleep(0.1)
            if cmd_ret:
                logging.info(s + ' is stopping!')
                services_start = services_start + 1
        pass
