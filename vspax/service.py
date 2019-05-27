import vspax
from mqtt_service import *
from vspax.tcp_client_h import TcpClientHander
from vspax.tcp_server_h import TcpServerHandler
from hbmqtt_broker.conf import MQTT_PROT

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"
match_api = re.compile(r'^@api/(.+)$')


class VSPAX_Service(BaseService):
    def __init__(self, manager):
        self._manager = manager
        mqtt_conn = "localhost:{0}".format(MQTT_PROT)
        BaseService.__init__(self, mqtt_conn, {
            "api": "v1/vspax/api",
        })

    def start(self):
        BaseService.start(self)

    @whitelist.__func__
    def api_reset_bus(self, id, params):
        reset = self._manager.reset_bus()
        return self.success("api", id, {"result": reset})

    @whitelist.__func__
    def api_list(self, id, params):
        ports = self._manager.list_all()
        return self.success("api", id, ports)

    @whitelist.__func__
    def api_list_vir(self, id, params):
        ports = self._manager.list_vir()
        return self.success("api", id, ports)

    @whitelist.__func__
    def api_list_used(self, id, params):
        ports = self._manager.list_ports()
        return self.success("api", id, ports)

    @whitelist.__func__
    def api_add(self, id, params):
        port_name = params.name
        peer = params.get("peer")
        if not peer:
            raise NotFound("peer_not_found")
        handler = None
        if peer.get("type") == "tcp_client":
            handler = TcpClientHander(port_name, peer.get("host"), peer.get("port"), peer.get("info"))
        if peer.get("type") == "tcp_server":
            handler = TcpServerHandler(port_name, peer.get("host"), peer.get("port"), peer.get("info"))

        ret = self._manager.add(handler)
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, vspax.GetLastErrorMessage())

    @whitelist.__func__
    def api_remove(self, id, params):
        port_name = params.name
        ret = self._manager.remove(port_name)
        if ret:
            return self.api_list_vir(id, {})
        else:
            return self.failure("api", id, "Failed to remove port: {0}".format(port_name))

    @whitelist.__func__
    def api_info(self, id, params):
        port_name = params.name
        ret = self._manager.info(port_name)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "port_no_found")

    @whitelist.__func__
    def api_keep_alive(self, id, params):
        _enable_heartbeat = params.enable_heartbeat
        _heartbeat_timeout = params.heartbeat_timeout
        ret = self._manager.enable_heartbeat(_enable_heartbeat, _heartbeat_timeout)
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "error")
