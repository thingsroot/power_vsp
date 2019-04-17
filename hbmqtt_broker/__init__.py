import logging
import asyncio
import threading
from hbmqtt.broker import Broker

_broker_config = {
    "listeners": {
        "default": {
            "max-connections": 8,
            "type": "tcp"
        },
        "my-tcp-1": {
            "bind": "127.0.0.1:7883"
        },
        "my-ws-1": {
            "bind": "127.0.0.1:7884",
            "type": "ws"
        }
    },
    "timeout-disconnect-delay": 2,
    "auth": {
        "allow-anonymous": True
    },
    "plugins": [
        "auth_anonymous"
    ],
    "topic-check" : {
        "enabled": True,
        "plugins": ["topic_taboo"]
    }
}

@asyncio.coroutine
def broker_coro(broker_config):
    broker = Broker(broker_config)
    yield from broker.start()


class MQTTBroker(threading.Thread):
    def __init__(self, broker_config):
        threading.Thread.__init__(self)
        self._broker_config = broker_config

    def run(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(broker_coro(self._broker_config))
        loop.run_forever()


if __name__ == '__main__':
    formatter = "[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s"
    logging.basicConfig(level=logging.INFO, format=formatter)
    asyncio.get_event_loop().run_until_complete(broker_coro(_broker_config))
    asyncio.get_event_loop().run_forever()