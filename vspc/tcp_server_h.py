import select
import socket
import threading
import queue
import logging
from vspc.handler import Handler


class TcpServerHandler(Handler, threading.Thread):
    def __init__(self, host, port):
        self._clients = []
        self._servers = []
        self._manager = None
        self._host = host
        self._port = port
        self._thread_stop = False
        Handler.__init__(self)
        threading.Thread.__init__(self)

    def start(self):
        try:
            server = socket.socket()
            server.setblocking(0)

            server.bind((self._host, self._port))
            server.listen(5)
            self._servers.append(server)
            self._clients.append(server)
            threading.Thread.start(self)
        except Exception as ex:
            logging.exception(ex)
            return None

    def run(self):
        outputs = []
        message_queues = {}
        while not self._thread_stop:
            readable, writeable, exeptional = select.select(self._clients, outputs, self._clients)
            for s in readable:
                if s is self._servers:
                    conn, client_addr = s.accept()
                    conn.setblocking(0)
                    self._clients.append(conn)
                    message_queues[conn] = queue.Queue()
                else:
                    data = s.recv(1024)
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

        for server in self._servers:
            server.close()

    def on_recv(self, data):
        for client in self._clients:
            client.send(data)