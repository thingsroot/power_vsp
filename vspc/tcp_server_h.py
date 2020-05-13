import select
import socket
import threading
import queue
import logging
from vspc.handler import Handler


class TcpServerHandler(Handler, threading.Thread):
    def __init__(self, host, port, info):
        self._clients = []
        self._servers = []
        self._manager = None
        self._host = host
        self._port = port
        self._info = info
        self._sock_host = None
        self._sock_port = 0
        self._peer_host = None
        self._peer_port = 0
        self._peer_send_count = 0
        self._peer_recv_count = 0
        self._thread_stop = False
        Handler.__init__(self)
        threading.Thread.__init__(self)

    def start(self):
        try:
            server = socket.socket()
            server.setblocking(0)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            server.bind((self._host, self._port))
            server.listen(5)
            self._sock_host, self._sock_port = s.getsockname()
            self._peer_state = 'LISTENING'
            self._servers.append(server)
            self._clients.append(server)
            Handler.start(self)
            threading.Thread.start(self)
        except Exception as ex:
            logging.exception(ex)
            return None

    def stop(self):
        self._thread_stop = True
        self.join(2)
        Handler.stop(self)

    def run(self):
        outputs = []
        message_queues = {}
        while not self._thread_stop:
            readable, writeable, exeptional = select.select(self._clients, outputs, self._clients, 1)
            for s in readable:
                if s is self._servers:
                    conn, client_addr = s.accept()
                    conn.setblocking(0)
                    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                    if len(self._clients) > 0:
                        print('TODO:')

                    self._peer_host, self._peer_port = conn.getpeername()
                    self._clients.append(conn)
                    self._peer_state = 'CONNECTED'
                    message_queues[conn] = queue.Queue()
                else:
                    data = s.recv(1024)
                    self._peer_recv_count += len(data)
                    self._stream_pub.socket_in_pub(self._port_key, data)
                    if data:
                        logging.debug("Data recevied {0}: {1}".format(s.getpeername()[0], data))
                        # message_queues[s].put(data)
                        # if s not in outputs:
                        #     outputs.append(s)
                        self.send(data)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        self._clients.remove(s)
                        if len(self._clients) == 0:
                            self._peer_host = None,
                            self._peer_port = 0
                        self._servers.remove(s)
                        del message_queues[s]

            for s in writeable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    logging.debug("client [%s] queue is empty.." % s.getpeername()[0])
                    outputs.remove(s)

                else:
                    logging.debug("sending msg to [%s]: " % s.getpeername()[0] +  next_msg)
                    s.send(next_msg.upper())

            for s in exeptional:
                logging.debug("handling exception for {0}".format(s.getpeername()))
                self._clients.remove(s)
                if s in outputs:
                    outputs.remove(s)
                    s.close()
                    del message_queues[s]

            if len(self._clients) == 0:
                self._peer_state = 'LISTENING'

        self._peer_state = 'CLOSED'
        for server in self._servers:
            server.close()

    def peer_dict(self):
        return {
            'type': 'tcp_server',
            'host': self._host,
            'port': self._port,
            'info': self._info,
            'sock_host': self._sock_host,
            'sock_port': self._sock_port,
            'peer_host': self._peer_host,
            'peer_port': self._peer_port,
            'peer_state': self._peer_state,
            'peer_recv_count': self._peer_recv_count,
            'peer_send_count': self._peer_send_count
        }

    def clean_count(self):
        self._peer_send_count = 0
        self._peer_recv_count = 0
        Handler.clean_count(self)

    def on_recv(self, data):
        for client in self._clients:
            sent_size = client.send(data)
            self._peer_send_count += sent_size
            self._stream_pub.socket_out_pub(data[0:sent_size])