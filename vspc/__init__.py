from ctypes import *
from ctypes.wintypes import *

api = CDLL("ftvspc.dll")

# FtVspc_LicenseType
(ftvspcLicenseDemo, ftvspcLicenseDeveloper, ftvspcLicenseOem, ftvspcLicenseUser) = (0, 1, 2, 3)
# FtVspc_DataBits
(ftvspcDataBits5, ftvspcDataBits6, ftvspcDataBits7, ftvspcDataBits8) = (0, 1, 2, 3)
# FtVspc_Parity
(ftvspcParityNone, ftvspcParityOdd, ftvspcParityEven, ftvspcParityMark, ftvspcParitySpace) = (0, 1, 2, 3, 4)
# FtVspc_StopBits
(ftvspcStopBitsOne, ftvspcStopBitsOne5, ftvspcStopBitsTwo) = (0, 1, 2)
# FtVspc_Event
ftvspcEventThirdPartyPortCreate = 0
ftvspcEventThirdPartyPortRemove = 1
ftvspcEventPortCreate = 2
ftvspcEventPortRemove = 3
ftvspcEventTrialExpired = 100
ftvspcEventPortLimitExceeded = 101
ftvspcEventLicenseQuotaExceeded = 102

# FtVspc_PortEvent
ftvspcPortEventOpen = 0
ftvspcPortEventOpenBeforeAttach = 1
ftvspcPortEventQueryOpen = 2
ftvspcPortEventClose = 3
ftvspcPortEventRxChar = 4
ftvspcPortEventDtr = 5
ftvspcPortEventRts = 6
ftvspcPortEventBaudRate = 7
ftvspcPortEventDataBits = 8
ftvspcPortEventParity = 9
ftvspcPortEventStopBits = 10
ftvspcPortEventBreak = 11
ftvspcPortEventPurge = 12
ftvspcPortEventXonLim = 13
ftvspcPortEventXoffLim = 14
ftvspcPortEventXonChar = 15
ftvspcPortEventXoffChar = 16
ftvspcPortEventErrorChar = 17
ftvspcPortEventEofChar = 18
ftvspcPortEventEvtChar = 19
ftvspcPortEventBreakChar = 20
ftvspcPortEventTimeouts = 21
ftvspcPortEventOutxCtsFlow = 22  # fOutxCtsFlow			SERIAL_CTS_HANDSHAKE
ftvspcPortEventOutxDsrFlow = 23  # fOutxDsrFlow			SERIAL_DSR_HANDSHAKE
ftvspcPortEventDtrControl = 24  # fDtrControl			SERIAL_DTR_MASK = SERIAL_DTR_CONTROL | SERIAL_DTR_HANDSHAKE
ftvspcPortEventDsrSensitivity = 25  # fDsrSensitivity		SERIAL_DSR_SENSITIVITY
ftvspcPortEventTXContinueOnXoff = 26  # fTXContinueOnXoff	    SERIAL_XOFF_CONTINUE
ftvspcPortEventOutX = 27  # fOutX				    SERIAL_AUTO_TRANSMIT
ftvspcPortEventInX = 28  # fInX					SERIAL_AUTO_RECEIVE
ftvspcPortEventNull = 29  # fNull				    SERIAL_NULL_STRIPPING
ftvspcPortEventRtsControl = 30  # fRtsControl			SERIAL_RTS_MASK = SERIAL_RTS_CONTROL | SERIAL_RTS_HANDSHAKE | SERIAL_TRANSMIT_TOGGLE
ftvspcPortEventAbortOnError = 31  # fAbortOnError	    	SERIAL_ERROR_ABORT
ftvspcPortEventUseErrorChar = 32  # fErrorChar			SERIAL_ERROR_CHAR

# FtVspc_PortType
(ftvspcPortTypeSingle, ftvspcPortTypeOverlapped, ftvspcPortTypeTwin) = (0, 1, 2)

# VSPC Event, ulValue, Context
EventCB = WINFUNCTYPE(None, c_int, c_void_p, c_void_p)
# VSPC Port Event, ulValue, Context
PortEventCB = WINFUNCTYPE(c_void_p, c_int, c_void_p, c_void_p)


class FT_VSPC_APP(Structure):
    _fields_ = [
        ("dwPid", c_ulong),
        ("cAppPath", c_char * 260),
        ("wcAppPath", c_char * 260)
    ]


class FTVSPC_INFO(Structure):
    _fields_ = [
        ("unVspcInfoSize", c_uint),
        ("cVersion", c_char * 32),
        ("LicenseType", c_int),
        ("unNumberOfLicenses", c_uint),
        ("unNumberOfPorts", c_uint),
        ("unPortTrialTime", c_uint),
        ("cLicensedUser", c_char * 255),
        ("cLicensedCompany", c_char * 255),
        ("cExpirationDate", c_char * 64)
    ]


class FT_VSPC_PORT(Structure):
    _fields_ = [
        ("unPortNo", c_uint),
        ("cPortNameA", c_char * 35),
        ("cPortNameW", c_char * 35)
    ]


class COMMTIMEOUTS(Structure):
    _fields_ = [
        ("ReadIntervalTimeout", c_ulong),
        ("ReadTotalTimeoutMultiplier", c_ulong),
        ("ReadTotalTimeoutConstant", c_ulong),
        ("WriteTotalTimeoutMultiplier", c_ulong),
        ("WriteTotalTimeoutConstant", c_ulong)
    ]


FtVspcApiInit = api.FtVspcApiInitA
FtVspcApiInit.argtypes = [EventCB, c_void_p, c_char_p]
FtVspcApiInit.restype = c_int

FtVspcApiClose = api.FtVspcApiClose
FtVspcApiClose.argtypes = []
FtVspcApiClose.restype = None

FtVspcCreatePortByNum = api.FtVspcCreatePortByNum
FtVspcCreatePortByNum.argtype = [c_uint]
FtVspcCreatePortByNum.restype = c_int

FtVspcCreatePort = api.FtVspcCreatePortA
FtVspcCreatePort.argtypes = [c_char_p]
FtVspcCreatePort.restype = c_int

FtVspcAttach = api.FtVspcAttachA
FtVspcAttach.argtypes = [c_char_p, PortEventCB, c_void_p]
FtVspcAttach.restype = c_void_p

FtVspcAttachByNum = api.FtVspcAttachByNum
FtVspcAttachByNum.argtypes = [c_uint, PortEventCB, c_void_p]
FtVspcAttachByNum.restype = c_void_p

FtVspcRemovePort = api.FtVspcRemovePortA
FtVspcRemovePort.argtype = [c_char_p]
FtVspcCreatePort.restype = c_int

FtVspcRemovePortByNum = api.FtVspcRemovePortByNum
FtVspcAttachByNum.argtypes = [c_uint]
FtVspcAttachByNum.restype = c_void_p


def FtVspcGetInQueueBytes(handle):
    sz = c_ulong(0)
    ret = api.FtVspcGetInQueueBytes(handle, byref(sz))
    if ret != 1:
        return
    return sz.value


def FtVspcRead(PortHandle, Len):
    s = create_string_buffer(b'\000' * int(Len))
    ret_len = c_ulong(0)
    ret = api.FtVspcRead(PortHandle, s, Len, byref(ret_len))
    if (ret != 1):
        return None
    return s[0:ret_len.value]


def FtVspcWrite(PortHandle, Data):
    Data = Data.encode('utf-8')
    ret = api.FtVspcWrite(PortHandle, create_string_buffer(Data), len(Data))
    return ret == 1


def FtVspcGetInfo(info):
    return api.FtVspcGetInfoW(byref(info))


FtVspcGetLastError = api.FtVspcGetLastError
FtVspcGetLastError.artypes = []
FtVspcGetLastError.restype = c_int


def FtVspcGetErrorMessage(ErrorCode):
    s = create_string_buffer(b'\000' * 256)
    sz = api.FtVspcGetErrorMessageA(ErrorCode, pointer(s), 256)
    if sz > 0:
        return s[0, sz.value];
    return "UNKNOWN"
