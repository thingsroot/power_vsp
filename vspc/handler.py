import logging
import time
import struct
import binascii
from vspc import *
from helper import _dict, APPCtrl


BaudRate_map = {"110": 1, "300": 2, "600": 3, "1200": 4, "2400": 5, "4800": 6, "9600": 7, "19200": 8, "38400": 9,
    "57600": 10, "115200": 11, "460800": 12, "921600": 13}

class Handler:
    def __init__(self):
        self._port_key = None
        self._port_num = None
        self._port_name = None
        self._c_user_data = None
        self._recv_count = 0
        self._send_count = 0
        self._handle = None
        self._open_pid = None
        self._open_app = None
        self._attributes = {}
        self._stream_pub = None
        self._com_params = [0] * 6
        self._enable_packetheader = APPCtrl().get_packetheader()
        self._peer_state = 'INITIALIZED'

    def start(self):
        self._stream_pub.vspc_notify(self._port_key, 'ADD', {"name": self._port_num, "num": self._port_name})

    def stop(self):
        self._stream_pub.vspc_notify(self._port_key, 'REMOVE', {"name": self._port_num, "num": self._port_name})

    def is_port(self, name):
        return self._port_key == name or str(self._port_key) == name

    def set_port_key(self, key):
        self._port_key = key
        if type(self._port_key) == 'string':
            self._port_name = self._port_key
            self._port_num = self.get_port_num()
        else:
            self._port_num = self._port_key
            self._port_name = self.get_port_name()

    def get_port_key(self):
        return self._port_key

    def set_user_data(self, user_data):
        self._c_user_data = user_data

    def on_recv(self, data):
        pass

    def set_handle(self, handle):
        self._handle = handle

    def get_handle(self):
        return self._handle

    def set_stream_pub(self, stream_pub):
        self._stream_pub = stream_pub

    def peer_dict(self):
        pass

    def as_dict(self):
        data = _dict({})
        data['name'] = self._port_key
        data['port_num'] = self._port_num
        data['port_name'] = self._port_name
        data['pid'] = self._open_pid
        data['app_path'] = self._open_app
        data['recv_count'] = self._recv_count
        data['send_count'] = self._send_count
        for key in self._attributes:
            data[key] = self._attributes.get(key)
        peer_data = self.peer_dict() or {}
        data.update(peer_data)
        return data

    def clean_count(self):
        self._recv_count = 0
        self._send_count = 0

    def on_event(self, event, ul_value):
        ## logging.info("Port {0} event {1} ul_value: {2}".format(self._port_key, int(event), repr(ul_value)))
        if event == ftvspcPortEventOpen:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            logging.info("Port {0} opened.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}".format(self._port_key, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath))
            self._open_pid = app.contents.dwPid
            self._open_app = str(app.contents.cAppPath, 'GB2312')
            return

        if event == ftvspcPortEventOpenBeforeAttach:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            logging.debug("Port {0} attached.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}".format(self._port_key, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath))
            return

        if event == ftvspcPortEventQueryOpen:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            logging.debug("Port {0} QueryOpen.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}".format(self._port_key, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath))
            return 1

        if event == ftvspcPortEventClose:
            logging.info("Port {0} Closed. {1}".format(self._port_key, ul_value))
            self._open_pid = -1
            self._open_app = ""

        if event == ftvspcPortEventRxChar:
            # logging.debug("Port {0} RxChar. {1}", self._port_key, ul_value)
            sz = FtVspcGetInQueueBytes(self._handle)
            data = FtVspcRead(self._handle, sz)
            if data:
                # print("send data to remote::", str(binascii.b2a_hex(fixedbin))[2:-1].upper(), str(binascii.b2a_hex(data))[2:-1].upper())
                if self._enable_packetheader:
                    fixedbin = b'\xfe'
                    for v in self._com_params:
                        fixedbin = fixedbin + struct.pack('b', v)
                    data = fixedbin + b'\xef' + data
                self.on_recv(data)
                if self._stream_pub:
                    self._recv_count += len(data)
                    self._stream_pub.vspc_in_pub(self._port_key, data)

        if event == ftvspcPortEventDtr:
            # logging.debug("Application has set DTR to:", ul_value)
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventRts:
            # logging.debug("Application has set RTS to:", ul_value)
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventBaudRate:
            logging.debug("Application has set baud rate to: {0}".format(ul_value))
            if BaudRate_map.get(str(ul_value)):
                self._com_params[0] = BaudRate_map.get(str(ul_value))
            else:
                logging.error("This BaudRate {0} is unsupported".format(str(ul_value)))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventDataBits:
            self._com_params[3] = ul_value
            logging.debug("Application has set data bits to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventParity:
            self._com_params[2] = ul_value
            logging.debug("Application has set parity to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventStopBits:
            self._com_params[1] = ul_value
            logging.debug("Application has set stopbits to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventBreak:
            if ul_value == 0:
                self._attributes[PortEventNames[event]] = 'CLEAR'
                logging.debug("Application has called ClearCommBreak")
            else:
                self._attributes[PortEventNames[event]] = 'MARK'
                logging.debug("Application has called SetCommBreak")

        if event == ftvspcPortEventPurge:
            logging.debug("Application has set PurgeComm to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value
            # TODO: wait for a while clear receives
            '''
            PURGE_RXABORT
            0x0002
            Terminates all outstanding overlapped read operations and returns immediately, even if the read operations have not been completed.
            PURGE_RXCLEAR
            0x0008
            Clears the input buffer (if the device driver has one).
            PURGE_TXABORT
            0x0001
            Terminates all outstanding overlapped write operations and returns immediately, even if the write operations have not been completed.
            PURGE_TXCLEAR
            0x0004
            '''

        if event == ftvspcPortEventXonLim:
            logging.debug("Application has set XonLim to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventXoffLim:
            logging.debug("Application has set XoffLim to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventXonChar:
            logging.debug("Application has set XonChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventXoffChar:
            logging.debug("Application has set XoffChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventErrorChar:
            logging.debug("Application has set ErrorChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventEofChar:
            logging.debug("Application has set EofChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventEvtChar:
            logging.debug("Application has set EvtChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventBreakChar:
            logging.debug("Application has set BreakChar to: {0}".format(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventTimeouts:
            timeouts = cast(ul_value, POINTER(COMMTIMEOUTS))
            self._attributes[PortEventNames[event]] = {
                "ReadIntervalTimeout": timeouts.contents.ReadIntervalTimeout,
                "ReadTotalTimeoutMultiplier": timeouts.contents.ReadTotalTimeoutMultiplier,
                "ReadTotalTimeoutConstant": timeouts.contents.ReadTotalTimeoutConstant,
                "WriteTotalTimeoutMultiplier": timeouts.contents.WriteTotalTimeoutMultiplier,
                "WriteTotalTimeoutConstant": timeouts.contents.WriteTotalTimeoutConstant,
            }

        if event == ftvspcPortEventOutxCtsFlow:
            logging.debug("Application has set OutxCtsFlow to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventOutxDsrFlow:
            logging.debug("Application has set OutxDsrFlow to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventDtrControl:
            logging.debug("Application has set DtrControl to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventDsrSensitivity:
            logging.debug("Application has set DsrSensitivity to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventTXContinueOnXoff:
            logging.debug("Application has set TXContinueOnXoff to:" + str(ul_value))

            self._attributes[PortEventNames[event]] = ul_value == 1
        if event == ftvspcPortEventOutX:
            logging.debug("Application has set OutX to:", ul_value)
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventInX:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set InX to:", ul_value)

        if event == ftvspcPortEventNull:
            logging.debug("Application has set Null to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventRtsControl:
            logging.debug("Application has set RtsControls to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value

        if event == ftvspcPortEventAbortOnError:
            logging.debug("Application has set AbortOnError to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        if event == ftvspcPortEventUseErrorChar:
            logging.debug("Application has set UseErrorChar to:" + str(ul_value))
            self._attributes[PortEventNames[event]] = ul_value == 1

        return 0

    def send(self, data):
        ret = FtVspcWrite(self._handle, data)
        if ret:
            self._send_count += len(data)
            if self._stream_pub:
                self._stream_pub.vspc_out_pub(self._port_key, data)
        else:
            logging.error("Write Return is not equal to data length")
        return ret

    def get_port_name(self):
        count = FtVspcEnumVirtual()
        for i in range(0, count):
            port_num, mark_for_deletion = FtVspcGetVirtualNum(i)
            if port_num == self._port_key:
                port_name, mark_for_deletion = FtVspcGetVirtual(i)
                return port_name
        return None

    def get_port_num(self):
        count = FtVspcEnumVirtual()
        for i in range(0, count):
            port_name, mark_for_deletion = FtVspcGetVirtual(i)
            if port_name == self._port_key:
                port_num, mark_for_deletion = FtVspcGetVirtualNum(i)
                return port_num
        return None