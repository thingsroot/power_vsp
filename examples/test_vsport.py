import logging
import time
from vspax.vs_port import VSPort
from vspax.tcp_client_h import TcpClientHander


if __name__ == "__main__":
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=formatter)

    port = VSPort('COM9')
    port.start()
    # peer_handler = TcpClientHander(port, "172.30.1.143", 2003, "")
    peer_handler = TcpClientHander(port, "bj.proxy.thingsroot.com", 23112, "")
    port.set_peer(peer_handler)

    while True:
        time.sleep(10)