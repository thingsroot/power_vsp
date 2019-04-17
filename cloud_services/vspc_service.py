import threading
import logging
import re
import vspc
from cloud_services import BaseService, whitelist
from vspc.manager import VSPCManager

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"
match_api = re.compile(r'^@api/(.+)$')


class VSPC_Service(BaseService):
    def __init__(self):
        self._manager = VSPCManager()
        BaseService.__init__(self, "localhost:1883", {
            "api": "v1/vspc/api",
        })

    def start(self):
        self._manager.start()
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
        if params.get("by_name") == 1:
            ret = self._manager.add(params.get("name"))
        else:
            ret = self._manager.add_by_num(params.get("num"))
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, vspc.GetLastErrorMessage())

    @whitelist.__func__
    def api_remove(self, id, params):
        if params.get("by_name") == 1:
            ret = self._manager.remove(params.get("name"))
        else:
            ret = self._manager.remove_by_num(params.get("num"))
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, vspc.GetLastErrorMessage())
