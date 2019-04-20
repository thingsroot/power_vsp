import logging
import threading
import socket
import time
from vspc.handler import Handler


class TcpClientHander(Handler, threading.Thread):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._sock_host = None
        self._sock_port = 0
        self._peer_host = None
        self._peer_port = 0
        self._thread_stop = False
        self._peer_send_count = 0
        self._peer_recv_count = 0
        Handler.__init__(self)
        threading.Thread.__init__(self)

    def start(self):
        Handler.start(self)
        threading.Thread.start(self)

    def stop(self):
        self._thread_stop = True
        self.join(1)
        Handler.stop(self)

    def run(self):
        while not self._thread_stop:
            try:
                self._peer_state = 'CONNECTING'
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                s.connect((self._host, self._port))
                self._sock_host, self._sock_port = s.getsockname()
                self._peer_host, self._peer_port = s.getpeername()
                self._peer_state = 'CONNECTED'
                self._socket = s
                while not self._thread_stop:
                    data = s.recv(1024)
                    self._peer_recv_count += len(data)
                    self._stream_pub.socket_in_pub(self._port_key, data)
                    if not data:
                        logging.error("Client [{0}:{1}] socket closed!!".format(self._host, self._port))
                        break
                    self.send(data)
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
                    self._sock_host, self._sock_port = None, 0
                    self._peer_host, self._peer_port = None, 0
                    time.sleep(3)
            except Exception as ex:
                logging.exception(ex)
                continue

    def peer_dict(self):
        return {
            'peer_state': self._peer_state,
            'target_host': self._host,
            'target_port': self._port,
            'sock_host': self._sock_host,
            'sock_port': self._sock_port,
            'peer_host': self._peer_host,
            'peer_port': self._peer_port,
            'peer_recv_count': self._peer_recv_count,
            'peer_send_count': self._peer_send_count
        }

    def clean_count(self):
        self._peer_send_count = 0
        self._peer_recv_count = 0
        Handler.clean_count(self)

    def on_recv(self, data):
        if self._socket:
            sent_size = self._socket.send(data)
            self._peer_send_count += sent_size
            self._stream_pub.socket_out_pub(self._port_key, data[0:sent_size])
        else:
            logging.warning("Socket is not connected!")

