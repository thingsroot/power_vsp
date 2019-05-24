import logging
import time
import threading
import pythoncom
from queue import Queue
import win32com.client
from ctypes import *
from vspax import *
from helper import _dict


class VSPortEventHandler:
    def OnBaudRate(self, lBaudRate): pass
    def OnDTR(self, bOn): pass
    def OnHandFlow(self, lControlHandleShake, lFlowReplace, lXonLimit, lXOffLimit): pass
    def OnLineControl(self, cStopBits, cParity, cWordLength): pass
    def OnOpenClose(self, bOpened): pass
    def OnRxChar(self, lCount): pass
    def OnRTS(self, bOn): pass
    def OnSpecialChars(self, cEofChar, cErrorChar, cBreakChar, cEventChar, cXOnChar, cXoffChar): pass
    def OnTimeouts(self,  lReadIntervalTimeout, lReadTotalTimeoutMultiplier, lReadTotalTimeoutConstant, lWriteTotalTimeoutMultiplier, lWriteTotalTimeoutConstant): pass
    def OnEvent(self, EvtMask): pass
    def OnBreak(self, bOn): pass


class VSPort(VSPortEventHandler, threading.Thread):
    def __init__(self, port_key):
        self._port_key = port_key
        self._recv_count = 0
        self._send_count = 0
        self._stream_pub = None
        self._peer = None
        self._queue = Queue()
        self._thread_stop = False
        threading.Thread.__init__(self)

    def set_peer(self, peer):
        self._peer = peer

    def init_vsport(self):
        this_handler = self

        class innerHandler:
            def __init__(self):
                self._handler = this_handler

            def OnBaudRate(self, lBaudRate):
                # print('OnBaudRate', lBaudRate)
                return self._handler.OnBaudRate(lBaudRate)

            def OnDTR(self, bOn):
                return self._handler.OnDTR(bOn)

            def OnHandFlow(self, lControlHandleShake, lFlowReplace, lXonLimit, lXOffLimit):
                return self._handler.OnHandFlow(lControlHandleShake, lFlowReplace, lXonLimit, lXOffLimit)

            def OnLineControl(self, cStopBits, cParity, cWordLength):
                return self._handler.OnLineControl(cStopBits, cParity, cWordLength)

            def OnOpenClose(self, bOpened):
                return self._handler.OnOpenClose(bOpened)

            def OnRxChar(self, lCount):
                return self._handler.OnRxChar(lCount)

            def OnRTS(self, bOn):
                return self._handler.OnRTS(bOn)

            def OnSpecialChars(self, cEofChar, cErrorChar, cBreakChar, cEventChar, cXOnChar, cXoffChar):
                return self._handler.OnSpecialChars(cEofChar, cErrorChar, cBreakChar, cEventChar, cXOnChar, cXoffChar)

            def OnTimeouts(self, lReadIntervalTimeout, lReadTotalTimeoutMultiplier, lReadTotalTimeoutConstant,
                           lWriteTotalTimeoutMultiplier, lWriteTotalTimeoutConstant):
                return self._handler.OnTimeouts(lReadIntervalTimeout, lReadTotalTimeoutMultiplier,
                                                lReadTotalTimeoutConstant, lWriteTotalTimeoutMultiplier,
                                                lWriteTotalTimeoutConstant)

            def OnEvent(self, EvtMask):
                # print('OnBaudROnEventate', EvtMask)
                return self._handler.OnEvent(EvtMask)

            def OnBreak(self, bOn):
                return self._handler.OnBreak(bOn)
        try:
            pythoncom.CoInitialize()
            self._vsport = win32com.client.DispatchWithEvents(VSPort_ActiveX_ProgID, innerHandler)
            logging.info("VSPort create port: {0}".format(self._port_key))
            bRet = self._vsport.CreatePort(self._port_key)
            if not bRet:
                logging.info("Already created, try to Attach to port: {0}".format(self._port_key))
                bRet = self._vsport.Attach(self._port_key)
            if not bRet:
                logging.error("Attach to port: {0} failed!!!".format(self._port_key))
                self._vsport.Delete()
                return False
            else:
                logging.info("Attached to port: {0}".format(self._port_key))
            self._vsport.PurgeQueue()
            if self._stream_pub:
                self._stream_pub.vspax_notify(self._port_key, 'ADD', {"name": self._port_key})
            return True
        except Exception as ex:
            logging.exception(ex)
            return False

    def close_vsport(self):
        try:
            logging.info("VSPort remove port: {0}".format(self._port_key))
            self._stream_pub.vspax_notify(self._port_key, 'REMOVE', {"name": self._port_key})
            self._vsport.Delete()
        except Exception as ex:
            logging.exception(ex)

    def is_port(self, name):
        return self._port_key == name or str(self._port_key) == name

    def get_port_key(self):
        return self._port_key

    def set_stream_pub(self, stream_pub):
        self._stream_pub = stream_pub

    def socket_out_pub(self, data):
        if self._stream_pub:
            self._stream_pub.socket_out_pub(self._port_key, data)

    def socket_in_pub(self, data):
        if self._stream_pub:
            self._stream_pub.socket_in_pub(self._port_key, data)

    def peer_dict(self):
        pass

    def as_dict(self):
        data = _dict({})
        data['name'] = self._port_key
        data['port_name'] = self._port_key
        data['pid'] = 111 # self._vsport.get_PortOpenAppId()
        data['app_path'] = 'AAA' # self._vsport.get_PortOpenAppPath()
        data['recv_count'] = self._recv_count
        data['send_count'] = self._send_count
        # data['BaudRate'] = self._vsport.get_Baudrate()
        # data['DataBits'] = self._vsport.get_Databits()
        # data['Parity'] = self._vsport.get_Parity()
        # data['StopBits'] = self._vsport.get_Stopbits()
        peer_data = self.peer_dict() or {}
        data.update(peer_data)
        return data

    def clean_count(self):
        self._recv_count = 0
        self._send_count = 0
        self._peer.clean_count()

    def send(self, data):
        self._queue.put(data)

    def write_to_vsport(self, data):
        #logging.info("Serial Write: {0}".format(len(data)))
        ret = self._vsport.WriteArray(bytearray(data))
        if ret > 0:
            if ret != len(data):
                logging.error("Write Return is not equal to data length")
            self._send_count += ret
        if ret and self._stream_pub:
            self._stream_pub.vspax_out_pub(self._port_key, data)
        return ret

    def OnRxChar(self, lCount):
        data = self._vsport.ReadArray(lCount)
        data = data.tobytes()
        if data:
            # logging.info("Serial Got: {0}".format(len(data)))
            if self._stream_pub:
                self._recv_count += len(data)
                self._stream_pub.vspax_in_pub(self._port_key, data)
            self._peer.on_recv(data)

    def start(self):
        threading.Thread.start(self)

    def run(self):
        try:
            self.init_vsport()
            self._peer.start()
            while not self._thread_stop:
                pythoncom.PumpWaitingMessages()
                try:
                    while not self._queue.empty():
                        data = self._queue.get_nowait()
                        self.write_to_vsport(data)
                except Exception as ex:
                    logging.exception(ex)
                    continue
        except Exception as ex:
            logging.exception(ex)
        self._peer.stop()
        self.close_vsport()

    def stop(self):
        self._thread_stop = True
        self.join(2)
