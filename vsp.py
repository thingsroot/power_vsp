import os
from time import sleep
from vspc import *

port_handle_map = {}


def VSPC_Event_CB(Event, ulValue, Context):
    if (Event == ftvspcEventThirdPartyPortCreate):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventThirdPartyPortRemove):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventPortCreate):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventPortRemove):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventTrialExpired):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventPortLimitExceeded):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    if (Event == ftvspcEventLicenseQuotaExceeded):
        port = cast(ulValue, POINTER(FT_VSPC_PORT))
    return


def VSPC_Port_Event_CB(PortEvent, ulValue, Context):
    print(PortEvent, ulValue, Context)
    handle = port_handle_map[Context]

    if (PortEvent == ftvspcPortEventOpen):
        app = cast(ulValue, POINTER(FT_VSPC_APP))
        print(app.dwPid)
        print(app.cAppPath)
        print(app.wcAppPath)
        return

    if (PortEvent == ftvspcPortEventOpenBeforeAttach):
        app = cast(ulValue, POINTER(FT_VSPC_APP))
        print(app.dwPid)
        print(app.cAppPath)
        print(app.wcAppPath)
        return

    if (PortEvent == ftvspcPortEventQueryOpen):
        app = cast(ulValue, POINTER(FT_VSPC_APP))
        print(app.dwPid)
        print(app.cAppPath)
        print(app.wcAppPath)
        return 1

    if (PortEvent == ftvspcPortEventClose):
        print("Port is closed!", ulValue, Context)

    if (PortEvent == ftvspcPortEventRxChar):
        if not handle:
            return
        sz = FtVspcGetInQueueBytes(handle)
        print(FtVspcRead(handle, sz))

    if (PortEvent == ftvspcPortEventDtr):
        print("Application has set DTR to:", ulValue)

    if (PortEvent == ftvspcPortEventRts):
        print("Application has set RTS to:", ulValue)

    if (PortEvent == ftvspcPortEventBaudRate):
        print("Application has set baud rate to:", ulValue)

    if (PortEvent == ftvspcPortEventDataBits):
        print("Application has set data bits to:", ulValue)

    if (PortEvent == ftvspcPortEventParity):
        print("Application has set parity to:", ulValue)

    if (PortEvent == ftvspcPortEventStopBits):
        print("Application has set stopbits to:", ulValue)

    if (PortEvent == ftvspcPortEventBreak):
        if ulValue == 0:
            print("Application has called ClearCommBreak")
        else:
            priont("Application has called SetCommBreak")

    if (PortEvent == ftvspcPortEventPurge):
        print("Application has set PurgeComm to:", ulValue)

    if (PortEvent == ftvspcPortEventXonLim):
        print("Application has set XonLim to:", ulValue)

    if (PortEvent == ftvspcPortEventXoffLim):
        print("Application has set XoffLim to:", ulValue)

    if (PortEvent == ftvspcPortEventXonChar):
        print("Application has set XonChar to:", ulValue)

    if (PortEvent == ftvspcPortEventXoffChar):
        print("Application has set XoffChar to:", ulValue)

    if (PortEvent == ftvspcPortEventErrorChar):
        print("Application has set ErrorChar to:", ulValue)

    if (PortEvent == ftvspcPortEventEofChar):
        print("Application has set EofChar to:", ulValue)

    if (PortEvent == ftvspcPortEventEvtChar):
        print("Application has set EvtChar to:", ulValue)

    if (PortEvent == ftvspcPortEventBreakChar):
        print("Application has set BreakChar to:", ulValue)

    if (PortEvent == ftvspcPortEventTimeouts):
        timeouts = cast(ulValue, POINTER(COMMTIMEOUTS))
        print("==============================")
        print(timeouts)
        print("==============================")

    if (PortEvent == ftvspcPortEventOutxCtsFlow):
        print("Application has set OutxCtsFlow to:", ulValue)

    if (PortEvent == ftvspcPortEventOutxDsrFlow):
        print("Application has set OutxDsrFlow to:", ulValue)

    if (PortEvent == ftvspcPortEventDtrControl):
        print("Application has set DtrControl to:", ulValue)

    if (PortEvent == ftvspcPortEventDsrSensitivity):
        print("Application has set DsrSensitivity to:", ulValue)

    if (PortEvent == ftvspcPortEventTXContinueOnXoff):
        print("Application has set TXContinueOnXoff to:", ulValue)

    if (PortEvent == ftvspcPortEventOutX):
        print("Application has set OutX to:", ulValue)

    if (PortEvent == ftvspcPortEventInX):
        print("Application has set InX to:", ulValue)

    if (PortEvent == ftvspcPortEventNull):
        print("Application has set Null to:", ulValue)

    if (PortEvent == ftvspcPortEventRtsControl):
        print("Application has set RtsControls to:", ulValue)

    if (PortEvent == ftvspcPortEventAbortOnError):
        print("Application has set AbortOnError to:", ulValue)

    if (PortEvent == ftvspcPortEventUseErrorChar):
        print("Application has set UseErrorChar to:", ulValue)

    return None


event_cb = EventCB(VSPC_Event_CB)
port_event_cb = PortEventCB(VSPC_Port_Event_CB)

ret = FtVspcApiInit(event_cb, None, None)

print("FtVspcApiInit:", ret)

ret = FtVspcCreatePort(b"COM4")

print("FtVspcCreatePort:", ret)
if (ret != 1):
    os.exit(0)

handle = FtVspcAttach(b"COM4", port_event_cb, 4)

print("FtVspcAttach:", handle)
port_handle_map[4] = handle

while True:
    FtVspcWrite(handle, "123456")
    sleep(5)

FtVspcApiClose()
