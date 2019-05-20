import threading
import logging
import json
import os
from mqtt_service import *
from hbmqtt_broker.conf import MQTT_PROT

API_RESULT = "@api/RESULT"
API_LIST = "@api/list"
match_api = re.compile(r'^@api/(.+)$')

class UPDATE_Service(BaseService):
    def __init__(self, manager):
        self._manager = manager
        mqtt_conn = "localhost:{0}".format(MQTT_PROT)
        BaseService.__init__(self, mqtt_conn, {
            "api": "v1/update/api",
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
    def api_servers_list(self, id, params):
        # print("params:", params)
        ret = self._manager.check_servers_list()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "no_servers")

    @whitelist.__func__
    def api_version(self, id, params):
        # print("params:", params)
        ret = self._manager.check_version
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "no_version")

    @whitelist.__func__
    def api_update(self, id, params):
        # print("params:", params)
        update_confirm = params.get('update_confirm')
        new_version = params.get('new_version')
        new_version_filename = params.get('new_version_filename')
        if update_confirm:
            update_url = "http://thingscloud.oss-cn-beijing.aliyuncs.com/freeioe_Rprogramming/freeioe_Rprogramming_" + new_version + ".zip"
            if new_version_filename:
                update_url = "http://thingscloud.oss-cn-beijing.aliyuncs.com/freeioe_Rprogramming/" + new_version_filename
            save_file = "./_update/freeioe_Rprogramming_lastest.zip"
            action_ret = self._manager.on_update(update_url, save_file)
            return self.success("api", id, action_ret)
        else:
            return self.failure("api", id, "no")

    @whitelist.__func__
    def api_update_status(self, id, params):
        # print("params:", params)
        ret = self._manager.check_update_status()
        if ret:
            return self.success("api", id, ret)
        else:
            return self.failure("api", id, "no")
