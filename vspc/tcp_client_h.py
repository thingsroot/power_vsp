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
        self._peer_send_count = 0
        self._peer_recv_count = 0
        Handler.__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        while not self._thread_stop:
            try:
                self._peer_state = 'CONNECTING'
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self._host, self._port))
                self._peer_local_port = s.getsockopt()
                self._peer_state = 'CONNECTED'
                self._socket = s
                while not self._thread_stop:
                    data = s.recv(1024)
                    self._peer_recv_count += len(data)
                    self._stream_pub.socket_in_pub(data)
                    if data:
                        self.send(data)
                    else:
                        logging.error("Client [{0}:{1}] socket closed!!".format(self._host, self._port))
                        break
                ## closed
                if self._socket:
                    self._peer_state = 'DISCONNECTED'
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

    def peer_dict(self):
        return {
            'local_host': self._host,
            'local_port': self._port,
            'peer_recv_count': self._peer_recv_count,
            'peer_send_count': self._peer_send_count
        }

    def on_recv(self, data):
        if self._socket:
            sent_size = self._socket.send(data)
            self._peer_send_count += sent_size
            self._stream_pub.socket_out_pub(data[0:sent_size])
        else:
            logging.warning("Socket is not connected!")

