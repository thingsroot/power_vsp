import select
import socket
import threading
import queue
import logging


class SocketManager(threading.Thread):
    def __init__(self):
        self._inputs = []
        self._servers = []
        self._manager = None
        threading.Thread.__init__(self)

    def start(self):
        self._manager = self.create_server(4123, "localhost")
        threading.Thread.start(self)

    def run(self):
        outputs = []
        message_queues = {}
        while True:
            readable, writeable, exeptional = select.select(self._inputs, outputs, self._inputs)
            for s in readable:
                if s is self._servers:
                    conn, client_addr = s.accept()
                    conn.setblocking(0)
                    self._inputs.append(conn)
                    message_queues[conn] = queue.Queue()
                else:
                    data = s.recv(1024)
                    if data:
                        print("收到来自[%s]的数据:" % s.getpeername()[0], data)
                        message_queues[s].put(data)
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        self._inputs.remove(s)
                        self._servers.remove(s)
                        del message_queues[s]
            for s in writeable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    print("client [%s]" % s.getpeername()[0], "queue is empty..")
                    outputs.remove(s)

                else:
                    print("sending msg to [%s]" % s.getpeername()[0], next_msg)
                    s.send(next_msg.upper())
            for s in exeptional:
                print("handling exception for ", s.getpeername())
                self._inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

    def create_server(self, port, host="0.0.0.0"):
        try:
            server = socket.socket()
            server.setblocking(0)

            server.bind((host,port))
            server.listen(5)
            self._servers.append(server)
            self._inputs.append(server)
            return server
        except Exception as ex:
            logging.exception(ex)
            return None

    def create_client(self, host, port):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            client.setblocking(0)
            self._inputs.append(client)
            return client
        except Exception as ex:
            logging.exception(ex)
            return None
