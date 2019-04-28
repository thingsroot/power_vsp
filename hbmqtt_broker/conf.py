
broker_config = {
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
    "topic-check": {
        "enabled": True,
        "plugins": ["topic_taboo"]
    }
}

MQTT_PROT = 7883
MQTT_WS_PORT = 7884