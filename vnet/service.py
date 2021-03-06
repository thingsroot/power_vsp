import threading
import logging
import json
from time import sleep
import os
from mqtt_service import *
from hbmqtt_broker.conf import MQTT_PROT

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"
match_api = re.compile(r'^@api/(.+)$')

frpc_proxy = {
    "bridge": {"type": "tcp", "local_ip": "127.0.0.1", "local_port": "665",
        "remote_port": "0", "use_encryption": "false", "use_compression": "true"},
    "router": {"type": "tcp", "local_ip": "127.0.0.1", "local_port": "666",
        "remote_port": "0", "use_encryption": "false", "use_compression": "true"}
}

class VNET_Service(BaseService):
    def __init__(self, manager):
        self._manager = manager
        mqtt_conn = "localhost:{0}".format(MQTT_PROT)
        BaseService.__init__(self, mqtt_conn, {
            "api": "v1/vnet/api",
        })

    def start(self):
        BaseService.start(self)

    @whitelist.__func__
    def api_ping(self, id, params):
        # print("params:", params)
        ret = 'pong'
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "no_found")

    @whitelist.__func__
    def api_checkenv(self, id, params):
        # print("params:", params)
        ret = self._manager.wmi_in_thread(self._manager.env_check)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_fixenv(self, id, params):
        # print("params:", params)
        ret = self._manager.env_fix()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_tapslist(self, id, params):
        # print("params:", params)
        ret = self._manager.wmi_in_thread(self._manager.list_taps)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_service_status(self, id, params):
        # print("params:", params)
        ret = self._manager.service_status()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "status error")

    @whitelist.__func__
    def api_service_start(self, id, params):
        # print("params:", params)
        curpath = os.getcwd()
        file = curpath + '\\vnet\\tinc\\_frpc\\frpc.ini'
        ret = None
        if params:
            # print(params.get('vnet_cfg'))
            # print(params.get('frps_cfg'))
            vnettype = params.vnet_cfg['net_mode']
            proxytype = "frpc"
            if params.get("proxytype"):
                proxytype = params.get("proxytype")
            if proxytype == "frpc":
                self._manager.wirte_common_frpcini(file, params.get('vnet_cfg'), params.get('frps_cfg'))
                proxy_cfg = {
                    params.vnet_cfg['gate_sn'] + '_tofreeioe' + vnettype: frpc_proxy[vnettype]
                    # params.vnet_cfg['gate_sn'] + '_' + vnettype + '_' + str(int(time.time())): frpc_proxy[vnettype]
                #     Adjustment frpc proxy name
                }
                self._manager.add_proxycfg_frpcini(file, proxy_cfg)
            else:
                if params.get('nps_cfg'):
                    nps_server = params.get('nps_cfg').get("server_addr")
                    nps_port = params.get('nps_cfg').get("server_port")
                    nps_vkey = params.get('nps_cfg').get("vkey")
                    npc_inscmd = curpath + '\\vnet\\tinc\\_npc\\npc.exe' + " install -server=" + nps_server + ":" + nps_port + "-vkey=" + nps_vkey
                    os.popen("sc dtop Npc")
                    sleep(0.01)
                    os.popen(npc_inscmd)
                    sleep(0.01)
                    os.popen("sc config Npc start= demand")
            prepend_tap_ret = self._manager.wmi_in_thread(self._manager.prepend_tap)
            if prepend_tap_ret:
                ret = self._manager.service_start(vnettype, proxytype)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "start error")

    @whitelist.__func__
    def api_service_stop(self, id, params):
        vnettype = params.vnet_cfg['net_mode']
        proxytype = "frpc"
        if params.get("proxytype"):
            proxytype = params.get("proxytype")
        ret = self._manager.service_stop(vnettype, proxytype)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "stop error")

    @whitelist.__func__
    def api_post_gate(self, id, params):
        # print("params:", params)
        output = params.get('output')
        if output == 'vnet_stop':
            peer_host = 'nothing'
            peer_port = 'nothing'
            auth_code = params.get('auth_code')
            logging.info('post vnet_stop to gate!')
            ret = self._manager.post_to_cloud(auth_code, output, peer_host, peer_port)
            if ret:
                return self.success("api", id, ret)
            else:
                return self.failure("api", id, "post error")
            pass
        elif output == 'vnet_config':
            query_proxy = None
            for i in range(3):
                logging.info(str(i)+' query local_proxy_status!')
                query_proxy = self._manager.local_proxy_status()
                if query_proxy:
                    break
                sleep(i + 2)
            if query_proxy:
                if query_proxy['status'] == 'running':
                    peer_host = query_proxy['remote_addr'].split(':')[0]
                    peer_port = query_proxy['remote_addr'].split(':')[1]
                    auth_code = params.get('auth_code')
                    logging.info('post vnet_start to gate!')
                    ret = self._manager.post_to_cloud(auth_code, output, peer_host, peer_port)
                    if ret:
                        return self.success("api", id, ret)
                    else:
                        return self.failure("api", id, "post error")
                else:
                    self._manager.clean_all()
                    return self.failure("api", id, "proxy error")
            else:
                self._manager.clean_all()
                return self.failure("api", id, "proxy None")
        else:
            self._manager.clean_all()
            return self.failure("api", id, "output error")

    @whitelist.__func__
    def api_write_frpc(self, id, params):
        # print("params:", params)
        curpath = os.getcwd()
        file = curpath + '\\vnet\\tinc\\_frpc\\frpc.ini'
        ret = self._manager.wirte_common_frpcini(file)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_local_proxy_status(self, id, params):
        # print("params:", params)
        ret = self._manager.local_proxy_status()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_cloud_proxy_status(self, id, params):
        # print("params:", params)
        ret = self._manager.cloud_proxy_status()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")

    @whitelist.__func__
    def api_keep_alive(self, id, params):
        _enable_heartbeat = params.get('enable_heartbeat')
        _heartbeat_timeout = params.get('heartbeat_timeout')
        auth_code = params.get('auth_code')
        gate_sn = params.get('gate_sn')
        if gate_sn and auth_code:
            ret = self._manager.enable_heartbeat(_enable_heartbeat, _heartbeat_timeout, auth_code, gate_sn)
            if ret:
                return self.success("api", id, ret)
            else:
                return self.failure("api", id, "error")
        else:
            return self.failure("api", id, "no gate_sn")
