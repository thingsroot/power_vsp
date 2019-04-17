import logging
import threading
import socket
from vspc.handler import Handler


class TcpClientHander(Handler, threading.Thread):
    def __init__(self, name, host, port):
        self._host = host
        self._port = port
        self._thread_stop = False
        Handler.__init__(self, name)
        threading.Thread.__init__(self)

    def run(self):
        while not self._thread_stop:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self._host, self._port))
                self._socket = s
                while not self._thread_stop:
                    data = s.recv(1024)
                    if data:
                        self.send(data)
                    else:
                        logging.error("Client [{0}:{1}] socket closed!!".format(self._host, self._port))
                        break
                ## closed
                if self._socket:
                    try:
                        self._socket.close()
                    except Exception as ex:
                        logging.exception(ex)
                        continue
            except Exception as ex:
                logging.exception(ex)
                continue

    def on_recv(self, data):
        if self._socket:
            self._socket.send(data)
        else:
            logging.warning("Socket is not connected!")

