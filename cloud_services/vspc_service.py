import threading
import logging
import re
import vspc
from cloud_services import *
from vspc.tcp_client_h import TcpClientHander
from vspc.tcp_server_h import TcpServerHandler
from vspc_conf import MQTT_PROT

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"
match_api = re.compile(r'^@api/(.+)$')


class VSPC_Service(BaseService):
    def __init__(self, manager):
        self._manager = manager
        mqtt_conn = "localhost:{0}".format(MQTT_PROT)
        BaseService.__init__(self, mqtt_conn, {
            "api": "v1/vspc/api",
        })

    def start(self):
        BaseService.start(self)

    @whitelist.__func__
    def api_list(self, id, params):
        count = vspc.FtVspcEnumPhysical()
        phy_ports = []
        for i in range(0, count):
            port_name = vspc.FtVspcGetPhysical(i)
            if port_name:
                phy_ports.append(port_name)
        count = vspc.FtVspcEnumVirtual()
        vir_ports = []
        for i in range(0, count):
            port_name = vspc.FtVspcGetVirtual(i)
            if port_name:
                vir_ports.append(port_name)
        return self.success("api", id, {
            "phy": phy_ports,
            "vir": vir_ports
        })

    @whitelist.__func__
    def api_list_phy(self, id, params):
        count = vspc.FtVspcEnumPhysical()
        ports = []
        for i in range(0, count):
            port_name = vspc.FtVspcGetPhysical(i)
            if port_name:
                ports.append(port_name)
        return self.success("api", id, ports)

    @whitelist.__func__
    def api_list_vir(self, id, params):
        count = vspc.FtVspcEnumVirtual()
        ports = []
        for i in range(0, count):
            port_name = vspc.FtVspcGetVirtual(i)
            if port_name:
                ports.append(port_name)
        return self.success("api", id, ports)

    @whitelist.__func__
    def api_add(self, id, params):
        port_name = params.name
        peer = params.get("peer")
        if not peer:
            raise NotFound("peer_not_found")
        handler = None
        if peer.get("type") == "tcp_client":
            handler = TcpClientHander(peer.get("host"), peer.get("port"))
        if peer.get("type") == "tcp_server":
            handler = TcpServerHandler(peer.get("host"), peer.get("port"))

        if params.get("by_name") == 1:
            ret = self._manager.add(port_name, handler)
        else:
            ret = self._manager.add_by_num(int(port_name), handler)
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, vspc.GetLastErrorMessage())

    @whitelist.__func__
    def api_remove(self, id, params):
        port_name = params.name
        if params.get("by_name") == 1:
            ret = self._manager.remove(port_name)
        else:
            ret = self._manager.remove_by_num(int(port_name))
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, vspc.GetLastErrorMessage())

    @whitelist.__func__
    def api_info(self, id, params):
        port_name = params.name
        ret = self._manager.info(port_name)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "port_no_found")
