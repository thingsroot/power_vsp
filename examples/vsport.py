import win32com.client
import pythoncom
import threading
import time

vsport_progid = "VSPort.VSPortAx.1"


class FakeVSPortEventHandler:
    def OnBaudRate(self, lBaudRate):
        print('OnBaudRate', lBaudRate)

    def OnDTR(self, bOn):
        print('OnDTR', bOn)

    def OnHandFlow(self, lControlHandleShake, lFlowReplace, lXonLimit, lXOffLimit):
        print('OnHandFlow', lControlHandleShake, lFlowReplace, lXonLimit, lXOffLimit)

    def OnLineControl(self, cStopBits, cParity, cWordLength):
        print('OnLineControl', cStopBits, cParity, cWordLength)

    def OnOpenClose(self, bOpened):
        print('OnOpenClose', bOpened)

    def OnRxChar(self, lCount):
        print('OnRxChar', lCount)

    def OnRTS(self, bOn):
        print('OnRTS', bOn)

    def OnSpecialChars(self, cEofChar, cErrorChar, cBreakChar, cEventChar, cXOnChar, cXoffChar):
        print('OnSpecialChars', cEofChar, cErrorChar, cBreakChar, cEventChar, cXOnChar, cXoffChar)

    def OnTimeouts(self,  lReadIntervalTimeout, lReadTotalTimeoutMultiplier, lReadTotalTimeoutConstant, lWriteTotalTimeoutMultiplier, lWriteTotalTimeoutConstant):
        print('OnTimeouts',  lReadIntervalTimeout, lReadTotalTimeoutMultiplier, lReadTotalTimeoutConstant, lWriteTotalTimeoutMultiplier, lWriteTotalTimeoutConstant)

    def OnEvent(self, EvtMask):
        print('OnEvent', EvtMask)

    def OnBreak(self, bOn):
        print('OnBreak', bOn)


class Handler(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        pythoncom.CoInitialize()
        vsport = win32com.client.DispatchWithEvents(vsport_progid, FakeVSPortEventHandler)

        vsport.ResetBus()  # method是Activex注册的方法.
        vsport.CreatePort("COM8")
        vsport.Attach("COM8")

        pythoncom.PumpMessages()  # 等待事件的发生


if __name__ == "__main__":
    h = Handler()
    h.start()
    while True:
        time.sleep(1)