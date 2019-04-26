import threading
import logging
import re
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
        ret = self._manager.info('pong')
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
            self._manager.wirte_common_frpcini(file, params.get('vnet_cfg'), params.get('frps_cfg'))
            vnettype = params.vnet_cfg['net_mode']
            proxy_cfg = {
                params.vnet_cfg['gate_sn'] + '_tofreeioe' + vnettype: frpc_proxy[vnettype]
            }
            self._manager.add_proxycfg_frpcini(file, proxy_cfg)

            prepend_tap_ret = self._manager.wmi_in_thread(self._manager.prepend_tap)
            if prepend_tap_ret:
                ret = self._manager.service_start(vnettype)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "start error")

    @whitelist.__func__
    def api_service_stop(self, id, params):
        vnettype = params.vnet_cfg['net_mode']
        ret = self._manager.service_stop(vnettype)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "stop error")

    @whitelist.__func__
    def api_post_gate(self, id, params):
        # print("params:", params)
        query_proxy = self._manager.local_proxy_status()
        output = params.get('output')
        if output == 'vnet_stop':
            peer_host = 'nothing'
            peer_port = 'nothing'
            auth_code = params.get('auth_code')
            ret = self._manager.post_to_cloud(auth_code, output, peer_host, peer_port)
            if ret:
                return self.success("api", id, ret)
            else:
                return self.failure("api", id, "post error")
            pass
        elif output == 'vnet_config':
            if query_proxy:
                if query_proxy['status'] == 'running':
                    peer_host = query_proxy['remote_addr'].split(':')[0]
                    peer_port = query_proxy['remote_addr'].split(':')[1]
                    auth_code = params.get('auth_code')
                    ret = self._manager.post_to_cloud(auth_code, output, peer_host, peer_port)
                    if ret:
                        return self.success("api", id, ret)
                    else:
                        return self.failure("api", id, "post error")
                else:
                    return self.failure("api", id, "proxy error")
            else:
                return self.failure("api", id, "proxy error")
        else:
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