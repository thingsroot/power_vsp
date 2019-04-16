
"""
Simple string reversal service using llama
"""

import logging

from llama import mqtt


REVERSE_REQUEST = "@strings/REVERSE_REQUEST"
REVERSE_SUCCESS = "@strings/REVERSE_SUCCESS"

def reverse_success(result):
    return {
        "type": REVERSE_SUCCESS,
        "payload": result,
    }


def _handle_reverse(string):
    """Reverse string"""
    logging.info("Reversing string: {}".format(string))

    return reverse_success(string[::-1])


def main():

    # Connect to MQTT broker and start dispatch loop
    dispatch, receive = mqtt.connect("localhost:1883", {
        "strings": "v1/simple/strings",
    })

    for action in receive():
        if action["type"] == REVERSE_REQUEST:
            dispatch(_handle_reverse(action["payload"]))


if __name__ == "__main__":
    main()

