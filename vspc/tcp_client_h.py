import logging
import threading
import socket
import time
from vspc.handler import Handler


class TcpClientHander(Handler, threading.Thread):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._thread_stop = False
        Handler.__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        while not self._thread_stop:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self._host, self._port))
                self._socket = s
                while not self._thread_stop:
                    data = s.recv(1024)
                    self._peer_recv_count += len(data)
                    if data:
                        self.send(data)
                    else:
                        logging.error("Client [{0}:{1}] socket closed!!".format(self._host, self._port))
                        break
                ## closed
                if self._socket:
                    try:
                        self._socket.close()
                        self._socket = None
                    except Exception as ex:
                        logging.exception(ex)
                        continue
                if not self._thread_stop:
                    time.sleep(3)
            except Exception as ex:
                logging.exception(ex)
                continue

    def on_recv(self, data):
        if self._socket:
            sent_size = self._socket.send(data)
            self._peer_send_count += sent_size
        else:
            logging.warning("Socket is not connected!")

