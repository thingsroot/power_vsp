import threading
import logging
import time
import json
import serial.tools.list_ports
from vspax.vs_port import VSPort


class VSPAXManager(threading.Thread):
    def __init__(self, stream_pub):
        threading.Thread.__init__(self)
        self._ports = []
        self._thread_stop = False
        self._mqtt_stream_pub = stream_pub
        self._enable_heartbeat = True
        self._heartbeat_timeout = time.time() + 90
        self._vsport_ctrl = None

    def list(self):
        return [handler.as_dict() for handler in self._ports]

    def list_ports(self):
        return [handler.get_port_key() for handler in self._ports]

    def list_all(self):
        return serial.tools.list_ports.comports()

    def list_vir(self):
        return self._vsport_ctrl.ListVir()

    def reset_bus(self):
        return self._vsport_ctrl.ResetBus()

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
        port = self.get(name)
        if not port:
            logging.error("Failed to find port {0}!!".format(name))
            return False

        port.stop()

        self._ports.remove(port)
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

    def run(self):
        self._vsport_ctrl = VSPort()
        self._vsport_ctrl.init()
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

        self._vsport_ctrl.close()
        logging.warning("VSPAX Manager Closed!!!")

    def stop(self):
        self._thread_stop = True
        self.join(3)

    def clean_all(self):
        keys = [h.get_port_key() for h in self._ports]
        for name in keys:
            try:
                self.remove(name)
            except Exception as ex:
                logging.exception(ex)
