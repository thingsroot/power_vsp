import os
import threading
import logging
from time import sleep
from vspc import *
from handler import Handler


class Manager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._handlers = []
        self._thread_stop = False

    def list(self):
        return [handler.name() for handler in self._handlers]

    def get(self, name):
        for handler in self._handlers:
            if handler.name() == name:
                return handler
        return None

    def get_port_event_cb(self, handler):
        def vspc_port_event_cb(port_event, ul_value, context):
            logging.trace(port_event, ul_value, context)
            handler.on_event(port_event, ul_value, context)

        return vspc_port_event_cb

    def add(self, name):
        port_name = create_string_buffer(name)

        ret = FtVspcCreatePort(port_name)

        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to create port {0}, reason: {1}".format(name, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Created port {0}".format(name))

        handler = Handler(name)
        port_event_cb = PortEventCB(self.get_port_event_cb(handler))

        handle = FtVspcAttach(port_name, port_event_cb, None)

        if ret.value != 1:
            logging.error("Failed to attach port {0}, reason: {1}".format(name, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Created port {0}".format(name))

        handler.set_handle(handle)
        self._handlers.append(handler)

        return True

    def add_by_num(self, num):
        ret = FtVspcCreatePortByNum(num)

        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to create port by num {0}, reason: {1}".format(num, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Created port by num{0}".format(num))

        handler = Handler(num)
        port_event_cb = PortEventCB(self.get_port_event_cb(handler))

        handle = FtVspcAttachByNum(num, port_event_cb)

        if ret.value != 1:
            logging.error("Failed to attach port by num {0}, reason: {1}".format(num, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Created port by num{0}".format(num))

        handler.set_handle(handle)
        self._handlers.append(handler)

        return True

    def remove(self, name):
        handler = None
        for h in self._handlers:
            if h.name() == name:
                handler = h

        if not handler:
            logging.error("Failed to find port {0}!!".format(name))
            return False

        ret = FtVspcDetach(handler.get_handle())

        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to detach port {0}, reason: {1}".format(name, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Removed port {0}".format(name))

        ret = FtVspcRemovePort(name)
        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to remove port {0}, reason: {1}".format(name, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Removed port {0}".format(name))

        self._handlers.remove(handler)
        return True

    def remove_by_num(self, num):
        handler = None
        for h in self._handlers:
            if h.name() == num:
                handler = h

        if not handler:
            logging.error("Failed to find port by num {0}!!".format(num))
            return False

        ret = FtVspcDetach(handler.get_handle())

        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to detach port by num {0}, reason: {1}".format(num, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Detach port by num {0}".format(num))

        ret = FtVspcRemovePortByNum(num)
        if ret.value != 0 and ret.value != 1:
            logging.error("Failed to remove port by num {0}, reason: {1}".format(num, FtVspcGetErrorMessage(ret)))
            return False
        else:
            logging.info("Removed port by num {0}".format(num))

        self._handlers.remove(handler)
        return True

    def get_event_cb(self):
        def vspc_event_cb(event, ul_value, context):
            self.on_event(event, ul_value, context)
        return vspc_event_cb

    def on_event(self, event, ul_value, context):
        port = None
        if event == ftvspcEventThirdPartyPortCreate:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventThirdPartyPortRemove:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventPortCreate:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventPortRemove:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventTrialExpired:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventPortLimitExceeded:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        if event == ftvspcEventLicenseQuotaExceeded:
            port = cast(ul_value, POINTER(FT_VSPC_PORT))
        logging.trace("VSPC_Event_CB: {0} {1} {2}".format(port, ul_value, context))
        return

    def run(self):
        event_cb = EventCB(self.get_event_cb())
        ret = FtVspcApiInit(event_cb, None, None)
        logging.trace("FtVspcApiInit:", ret)

        if ret != 1:
            logging.fatal("Failed to Initialize VSPC Library, ret ${0}".format(ret))
            return

        while not self._thread_stop:
            sleep(1)

        FtVspcApiClose()
        logging.warning("Close VSPC Library!!!")

    def stop(self):
        self._thread_stop = True
        self.join()

