import threading
import logging
import vspax
import time
import json
import pythoncom
import win32com.client
from vspax import *

class VSPAXManager(threading.Thread):
    def __init__(self, stream_pub):
        threading.Thread.__init__(self)
        self._ports = []
        self._thread_stop = False
        self._mqtt_stream_pub = stream_pub
        self._enable_heartbeat = True
        self._heartbeat_timeout = time.time() + 90

    def list(self):
        return [handler.as_dict() for handler in self._ports]

    def list_ports(self):
        return [handler.get_port_key() for handler in self._ports]

    def get(self, name):
        for handler in self._ports:
            if handler.is_port(name):
                return handler
        return None

    def add(self, port):
        port.set_stream_pub(self._mqtt_stream_pub)
        port.start()
        self._ports.append(port)

        return True

    def remove(self, name):
        handler = self.get(name)
        if not handler:
            logging.error("Failed to find port {0}!!".format(name))
            return False

        handler.stop()

        self._ports.remove(handler)
        return True

    def info(self, name):
        handler = self.get(name)
        if not handler:
            logging.error("Failed to find port {0}!!".format(name))
            return False
        return handler.as_dict()

    def enable_heartbeat(self, flag, timeout):
        self._enable_heartbeat = flag
        self._heartbeat_timeout = timeout + time.time()
        return {"enable_heartbeat": self._enable_heartbeat, "heartbeat_timeout": self._heartbeat_timeout}

    def reset_bus(self):
        pythoncom.CoInitialize()
        vsport = win32com.client.Dispatch(VSPort_ActiveX_ProgID)
        return vsport.ResetBus()

    def run(self):
        while not self._thread_stop:
            time.sleep(1)

            for handler in self._ports:
                try:
                    info = json.dumps(handler.as_dict())
                    self._mqtt_stream_pub.vspax_status(handler.get_port_key(), info)
                except Exception as ex:
                    logging.exception(ex)
            # print('timespan::::::::::::', time.time() - self._heartbeat_timeout)
            if self._enable_heartbeat and time.time() > self._heartbeat_timeout:
                pass #self.clean_all()

        logging.warning("Close VSPAX Library!!!")

    def stop(self):
        self._thread_stop = True
        self.join()

    def clean_all(self):
        keys = [h.get_port_key() for h in self._ports]
        for name in keys:
            try:
                self.remove(name)
            except Exception as ex:
                logging.exception(ex)
