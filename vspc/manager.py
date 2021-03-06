import threading
import logging
import vspc
import ctypes
import ctypes.wintypes
import time
import json
import requests
import os
from helper import APPCtrl


def vspc_event_cb(event, ul_value, context):
    manager = ctypes.cast(context, ctypes.POINTER(ctypes.py_object)).contents.value
    manager.on_event(event, ul_value)


def vspc_port_event_cb(event, ul_value, context):
    handler = ctypes.cast(context, ctypes.POINTER(ctypes.py_object)).contents.value
    r = handler.on_event(event, ul_value)
    if r is not None:
        return r
    else:
        return 0


class VSPCManager(threading.Thread):
    def __init__(self, stream_pub):
        threading.Thread.__init__(self)
        self._handlers = []
        self._thread_stop = False
        self._mqtt_stream_pub = stream_pub
        self._enable_heartbeat = APPCtrl().get_heartbeat()
        self._heartbeat_timeout = time.time() + 90
        self._vspc_event_cb = vspc.EventCB(vspc_event_cb)
        self._vspc_port_event_cb = vspc.PortEventCB(vspc_port_event_cb)

    def list(self):
        return [handler.as_dict() for handler in self._handlers]

    def get(self, name):
        for handler in self._handlers:
            if handler.is_port(name):
                return handler
        return None

    def add(self, name, handler):

        ret = vspc.FtVspcCreatePort(name)

        if not ret:
            logging.error("Failed to create port {0}, reason: {1}".format(name, vspc.GetLastErrorMessage()))
            return False
        else:
            logging.info("Created port {0}".format(name))

        # handler.set_info(port_info)

        cUserdata = ctypes.cast(ctypes.pointer(ctypes.py_object(handler)), ctypes.c_void_p)
        handler.set_user_data(cUserdata)
        handle = vspc.FtVspcAttach(name, self._vspc_port_event_cb, cUserdata)

        if not ret:
            logging.error("Failed to attach port {0}, reason: {1}".format(name, vspc.GetLastErrorMessage()))
            return False
        else:
            logging.info("Attached port {0}".format(name))

        handler.set_handle(handle)
        handler.set_port_key(name)
        handler.set_stream_pub(self._mqtt_stream_pub)
        handler.start()
        self._handlers.append(handler)

        return True

    def add_by_num(self, num, handler):
        ret = vspc.FtVspcCreatePortByNum(num)

        if not ret:
            logging.error("Failed to create port by num {0}, reason: {1}".format(num, vspc.GetLastErrorMessage()))
            return False
        else:
            logging.info("Created port by num{0}".format(num))

        # handler.set_info(port_info)

        cUserdata = ctypes.cast(ctypes.pointer(ctypes.py_object(handler)), ctypes.c_void_p)
        handler.set_user_data(cUserdata)
        handle = vspc.FtVspcAttachByNum(num, self._vspc_port_event_cb, cUserdata)

        if not ret:
            logging.error("Failed to attach port by num {0}, reason: {1}".format(num, vspc.GetLastErrorMessage()))
            return False
        else:
            logging.info("Attached port by num{0}".format(num))

        handler.set_handle(handle)
        handler.set_port_key(num)
        handler.set_stream_pub(self._mqtt_stream_pub)
        handler.start()
        self._handlers.append(handler)

        return True

    def remove(self, name):
        handler = self.get(name)
        if not handler:
            logging.error("Failed to find port {0}!!".format(name))
            return False

        handler.stop()

        ret = vspc.FtVspcDetach(handler.get_handle())

        if not ret:
            logging.error("Failed to detach {0}, reason: {1}".format(name, vspc.GetLastErrorMessage()))
            # return False
        else:
            logging.info("Removed port {0}".format(name))

        ret = vspc.FtVspcRemovePort(name)
        if not ret:
            logging.error("Failed to remove port {0}, reason: {1}".format(name, vspc.GetLastErrorMessage()))
            # return False
        else:
            logging.info("Removed port {0}".format(name))

        self._handlers.remove(handler)
        return True

    def remove_by_num(self, num):
        handler = self.get(num)
        if not handler:
            logging.error("Failed to find port by num {0}!!".format(num))
            return False

        ret = vspc.FtVspcDetach(handler.get_handle())

        if not ret:
            logging.error("Failed to detach port by num {0}, reason: {1}".format(num, vspc.GetLastErrorMessage()))
            # return False # Remove handler even we meet detaching error
        else:
            logging.info("Detach port by num {0}".format(num))

        ret = vspc.FtVspcRemovePortByNum(num)
        if not ret:
            logging.error("Failed to remove port by num {0}, reason: {1}".format(num, vspc.GetLastErrorMessage()))
            # return False # Remove handler even we meet removal error
        else:
            logging.info("Removed port by num {0}".format(num))

        self._handlers.remove(handler)

        return True

    def info(self, name):
        handler = self.get(name)
        if not handler:
            logging.error("Failed to find port {0}!!".format(name))
            return False
        return handler.as_dict()

    def enable_heartbeat(self, flag, timeout,  auth_code, gate_sn):
        self._enable_heartbeat = flag
        self._heartbeat_timeout = timeout + time.time()
        self.keep_vspc_alive(auth_code, gate_sn)
        return {"enable_heartbeat": self._enable_heartbeat, "heartbeat_timeout": self._heartbeat_timeout}

    def keep_vspc_alive(self,  auth_code, gate_sn):
        if gate_sn and auth_code:
            rand_id = gate_sn + '/send_output/heartbeat_timeout/' + str(time.time())
            url = 'http://ioe.thingsroot.com'
            datas = {
                "id": rand_id,
                "device": gate_sn,
                "data": {
                    "device": gate_sn + ".freeioe_Vserial",
                    "output": 'heartbeat_timeout',
                    "value": 60,
                    "prop": "value"
                }
            }
            ret = self.action_send_output(url, auth_code, datas)

    def action_send_output(self, ioeurl, Authcode, send_data):
        url = ioeurl + '/api/method/iot.device_api.send_output'
        headers = {'AuthorizationCode': Authcode, 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(send_data))
        ret_content = None
        if response:
            ret_content = json.loads(response.content.decode("utf-8"))
        return ret_content

    def on_event(self, event, ul_value):
        port = None
        if event == vspc.ftvspcEventThirdPartyPortCreate:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventThirdPartyPortRemove:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventPortCreate:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventPortRemove:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventTrialExpired:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventPortLimitExceeded:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        if event == vspc.ftvspcEventLicenseQuotaExceeded:
            port = ctypes.cast(ul_value, ctypes.POINTER(vspc.FT_VSPC_PORT))
        logging.debug("VSPC_Event_CB: {0} {1}".format(port, ul_value))
        return

    def run(self):
        cUserdata = ctypes.cast(ctypes.pointer(ctypes.py_object(self)), ctypes.c_void_p)
        key = """"""
        try:
            import license
            key = license.key
        except Exception as ex:
            logging.warning("Failed to loading license key!!")
        ret = vspc.FtVspcApiInit(self._vspc_event_cb, cUserdata, key)
        logging.info("FtVspcApiInit: {0}".format(ret))
        self._cUserdata = cUserdata

        if not ret:
            logging.fatal("Failed to Initialize VSPC Library: {0}".format(vspc.GetLastErrorMessage()))
            os.exit(0)
            return
        ret = vspc.FtVspcGetInfo()
        logging.info("FtVspcGetInfo: {0}".format(ret))
        # self.add_by_num(4, Handler(name))

        while not self._thread_stop:
            time.sleep(1)

            for handler in self._handlers:
                try:
                    info = json.dumps(handler.as_dict())
                    self._mqtt_stream_pub.vspc_status(handler.get_port_key(), info)
                except Exception as ex:
                    logging.exception(ex)
            # print('timespan::::::::::::', time.time() - self._heartbeat_timeout)
            if self._enable_heartbeat and time.time() > self._heartbeat_timeout:
                pass
                self.clean_all()

        vspc.FtVspcApiClose()
        logging.warning("Close VSPC Library!!!")

    def stop(self):
        self._thread_stop = True
        self.join()

    def clean_all(self):
        keys = [h.get_port_key() for h in self._handlers]
        for name in keys:
            try:
                self.remove(name)
            except Exception as ex:
                logging.exception(ex)
