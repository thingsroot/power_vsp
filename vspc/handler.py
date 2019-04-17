import logging
from vspc import *
from helper import _dict


class Handler:
    def __init__(self):
        self._port_key = None
        self._c_user_data = None
        self._recv_count = 0
        self._send_count = 0
        self._handle = None
        self._open_pid = None
        self._open_app = None
        self._attributes = {}
        self._stream_pub = None

    def is_port(self, name):
        return self._port_key == name or str(self._port_key) == name

    def set_port_key(self, key):
        self._port_key = key

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

    def as_dict(self):
        data = _dict({})
        data['name'] = self._name
        data['pid'] = self._open_pid
        data['app_path'] = self._open_app
        data['recv_count'] = self._recv_count
        data['send_count'] = self._send_count
        for key in self._attributes:
            data[key] = self._attributes.get(key)
        return data

    def on_event(self, event, ul_value):
        if event == ftvspcPortEventOpen:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            self._open_pid = app.contents.dwPid
            self._open_app = str(app.contents.cAppPath, 'GB2312')
            logging.debug("Port {0} opened.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}",
                          self._name, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath)
            return

        if event == ftvspcPortEventOpenBeforeAttach:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            logging.debug("Port {0} attached.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}",
                          self._name, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath)
            return

        if event == ftvspcPortEventQueryOpen:
            app = cast(ul_value, POINTER(FT_VSPC_APP))
            logging.debug("Port {0} QueryOpen.\t dwPid: {1} cAppPath: {2} wcAppPath: {3}",
                          self._name, app.contents.dwPid, app.contents.cAppPath, app.contents.wcAppPath)
            return 1

        if event == ftvspcPortEventClose:
            self._open_pid = -1
            self._open_app = ""
            logging.debug("Port {0} Closed. {1}}", self._name, ul_value)

        if event == ftvspcPortEventRxChar:
            logging.debug("Port {0} RxChar. {1}}", self._name, ul_value)
            sz = FtVspcGetInQueueBytes(self._handle)
            data = FtVspcRead(self._handle, sz)

            if data:
                if self._stream_pub:
                    self._stream_pub.vspc_out_pub(self._name, data)
                self.on_recv(data)

        if event == ftvspcPortEventDtr:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set DTR to:", ul_value)

        if event == ftvspcPortEventRts:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set RTS to:", ul_value)

        if event == ftvspcPortEventBaudRate:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set baud rate to:", ul_value)

        if event == ftvspcPortEventDataBits:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set data bits to:", ul_value)

        if event == ftvspcPortEventParity:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set parity to:", ul_value)

        if event == ftvspcPortEventStopBits:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set stopbits to:", ul_value)

        if event == ftvspcPortEventBreak:
            if ul_value == 0:
                self._attributes[PortEventNames[event]] = 'CLEAR'
                logging.debug("Application has called ClearCommBreak")
            else:
                self._attributes[PortEventNames[event]] = 'MARK'
                logging.debug("Application has called SetCommBreak")

        if event == ftvspcPortEventPurge:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set PurgeComm to:", ul_value)

        if event == ftvspcPortEventXonLim:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set XonLim to:", ul_value)

        if event == ftvspcPortEventXoffLim:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set XoffLim to:", ul_value)

        if event == ftvspcPortEventXonChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set XonChar to:", ul_value)

        if event == ftvspcPortEventXoffChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set XoffChar to:", ul_value)

        if event == ftvspcPortEventErrorChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set ErrorChar to:", ul_value)

        if event == ftvspcPortEventEofChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set EofChar to:", ul_value)

        if event == ftvspcPortEventEvtChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set EvtChar to:", ul_value)

        if event == ftvspcPortEventBreakChar:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set BreakChar to:", ul_value)

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
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set OutxCtsFlow to:", ul_value)

        if event == ftvspcPortEventOutxDsrFlow:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set OutxDsrFlow to:", ul_value)

        if event == ftvspcPortEventDtrControl:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set DtrControl to:", ul_value)

        if event == ftvspcPortEventDsrSensitivity:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set DsrSensitivity to:", ul_value)

        if event == ftvspcPortEventTXContinueOnXoff:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set TXContinueOnXoff to:", ul_value)

        if event == ftvspcPortEventOutX:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set OutX to:", ul_value)

        if event == ftvspcPortEventInX:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set InX to:", ul_value)

        if event == ftvspcPortEventNull:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set Null to:", ul_value)

        if event == ftvspcPortEventRtsControl:
            self._attributes[PortEventNames[event]] = ul_value
            logging.debug("Application has set RtsControls to:", ul_value)

        if event == ftvspcPortEventAbortOnError:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set AbortOnError to:", ul_value)

        if event == ftvspcPortEventUseErrorChar:
            self._attributes[PortEventNames[event]] = ul_value == 1
            logging.debug("Application has set UseErrorChar to:", ul_value)

        return None

    def send(self, data):
        ret = FtVspcWrite(self._handle, data)
        if ret and self._stream_pub:
            self._stream_pub.vspc_out_pub(self._name, data)
        return ret

