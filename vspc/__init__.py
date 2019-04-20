import logging
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
ftvspcPortEventOutxCtsFlow = 22         # fOutxCtsFlow			SERIAL_CTS_HANDSHAKE
ftvspcPortEventOutxDsrFlow = 23         # fOutxDsrFlow			SERIAL_DSR_HANDSHAKE
ftvspcPortEventDtrControl = 24          # fDtrControl			SERIAL_DTR_MASK = SERIAL_DTR_CONTROL | SERIAL_DTR_HANDSHAKE
ftvspcPortEventDsrSensitivity = 25      # fDsrSensitivity		SERIAL_DSR_SENSITIVITY
ftvspcPortEventTXContinueOnXoff = 26    # fTXContinueOnXoff	    SERIAL_XOFF_CONTINUE
ftvspcPortEventOutX = 27                # fOutX				    SERIAL_AUTO_TRANSMIT
ftvspcPortEventInX = 28                 # fInX					SERIAL_AUTO_RECEIVE
ftvspcPortEventNull = 29                # fNull				    SERIAL_NULL_STRIPPING
ftvspcPortEventRtsControl = 30          # fRtsControl			SERIAL_RTS_MASK = SERIAL_RTS_CONTROL | SERIAL_RTS_HANDSHAKE | SERIAL_TRANSMIT_TOGGLE
ftvspcPortEventAbortOnError = 31        # fAbortOnError	    	SERIAL_ERROR_ABORT
ftvspcPortEventUseErrorChar = 32        # fErrorChar			SERIAL_ERROR_CHAR

PortEventNames = [
    "Open",   # 0
    "OpenBeforeAttach",   # 1
    "QueryOpen",   # 2
    "Close",   # 3
    "RxChar",   # 4
    "Dtr",   # 5
    "Rts",   # 6
    "BaudRate",   # 7
    "DataBits",   # 8
    "Parity",   # 9
    "StopBits",   # 10
    "Break",   # 11
    "Purge",   # 12
    "XonLim",   # 13
    "XoffLim",   # 14
    "XonChar",   # 15
    "XoffChar",   # 16
    "ErrorChar",   # 17
    "EofChar",   # 18
    "EvtChar",   # 19
    "BreakChar",   # 20
    "Timeouts",   # 21
    "OutxCtsFlow",   # 22         # fOutxCtsFlow			SERIAL_CTS_HANDSHAKE
    "OutxDsrFlow",   # 23         # fOutxDsrFlow			SERIAL_DSR_HANDSHAKE
    "DtrControl",   # 24          # fDtrControl			SERIAL_DTR_MASK",   # SERIAL_DTR_CONTROL | SERIAL_DTR_HANDSHAKE
    "DsrSensitivity",   # 25      # fDsrSensitivity		SERIAL_DSR_SENSITIVITY
    "TXContinueOnXoff",   # 26    # fTXContinueOnXoff	    SERIAL_XOFF_CONTINUE
    "OutX",   # 27                # fOutX				    SERIAL_AUTO_TRANSMIT
    "InX",   # 28                 # fInX					SERIAL_AUTO_RECEIVE
    "Null",   # 29                # fNull				    SERIAL_NULL_STRIPPING
    "RtsControl",   # 30          # fRtsControl			SERIAL_RTS_MASK",   # SERIAL_RTS_CONTROL | SERIAL_RTS_HANDSHAKE | SERIAL_TRANSMIT_TOGGLE
    "AbortOnError",   # 31        # fAbortOnError	    	SERIAL_ERROR_ABORT
    "UseErrorChar",   # 32        # fErrorChar			SERIAL_ERROR_CHAR
]

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


def FtVspcApiClose():
    api.FtVspcApiClose()


def FtVspcApiInit(event_cb_func, context, license_key):
    license_key = license_key and create_string_buffer(license_key.encode('utf-8')) or None
    ret = api.FtVspcApiInitA(event_cb_func, context, license_key)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcApplyKey(license_key):
    ret = api.FtVspcApplyKeyA(create_string_buffer(license_key.encode('utf-8')))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcGetLastError():
    ret = api.FtVspcGetLastError()
    return ret


def FtVspcGetErrorMessage(ErrorCode):
    s = create_string_buffer(b'\000' * 1024)
    sz = api.FtVspcGetErrorMessageA(ErrorCode, pointer(s), 1024)
    if sz > 0:
        return s.value.decode('utf-8')
    return "UNKNOWN"


def print_api_error():
    eno = api.FtVspcGetLastError()
    logging.error("VSPC ERROR: {0}".format(FtVspcGetErrorMessage(eno)))

def GetLastErrorMessage():
    eno = api.FtVspcGetLastError()
    return FtVspcGetErrorMessage(eno)


def FtVspcEnumPhysical():
    s = c_int(0)
    ret = api.FtVspcEnumPhysical(pointer(s))
    if ret == 0:
        print_api_error()
        return None
    return s.value


def FtVspcEnumVirtual():
    s = c_int(0)
    ret = api.FtVspcEnumVirtual(pointer(s))
    if ret == 0:
        print_api_error()
        return None
    return s.value


def FtVspcGetPhysical(index):
    s = create_string_buffer(b'\000' * 256)
    ret = api.FtVspcGetPhysicalA(index, pointer(s), 256)
    if ret == 0:
        print_api_error()
        return None
    return s.value.decode('utf-8')


def FtVspcGetPhysicalNum(index):
    port_no = c_uint(0)
    ret = api.FtVspcGetPhysicalNum(index, pointer(port_no))
    if ret == 0:
        print_api_error()
        return None
    return port_no


def FtVspcGetVirtual(index):
    s = create_string_buffer(b'\000' * 256)
    marked_for_deletion = c_uint(0)
    ret = api.FtVspcGetVirtualA(index, pointer(s), 256, pointer(marked_for_deletion))
    if ret == 0:
        print_api_error()
        return None
    return s.value.decode('utf-8'), marked_for_deletion != 0


def FtVspcGetVirtualNum(index):
    port_no = c_uint(0)
    marked_for_deletion = c_uint(0)
    ret = api.FtVspcGetVirtualNum(index, pointer(port_no), pointer(marked_for_deletion))
    if ret == 0:
        print_api_error()
        return None
    return port_no.value, marked_for_deletion != 0


def FtVspcCreatePort(port_name):
    ret = api.FtVspcCreatePortA(create_string_buffer(port_name.encode('utf-8')))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreatePortEx(port_name, friendly_name, company_name):
    ret = api.FtVspcCreatePortExA(create_string_buffer(port_name),
                                  create_string_buffer(friendly_name),
                                  create_string_buffer(company_name))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreatePortByNum(num):
    ret = api.FtVspcCreatePortByNum(num)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreatePortOverlapped(name, real_alias):
    ret = api.FtVspcCreatePortOverlappedA(create_string_buffer(name),
                                          create_string_buffer(real_alias))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreatePortOverlappedEx(name, real_alias, friendly_name, company_name):
    ret = api.FtVspcCreatePortOverlappedExA(create_string_buffer(name),
                                            create_string_buffer(real_alias),
                                            create_string_buffer(friendly_name),
                                            create_string_buffer(company_name))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreatePortOverlappedByNum(num, real_alias):
    ret = api.FtVspcCreatePortOverlappedByNumA(num,
                                               create_string_buffer(real_alias))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreateTwinPort(name, real_alias):
    ret = api.FtVspcCreateTwinPortA(create_string_buffer(name),
                                    create_string_buffer(real_alias))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreateTwinPortEx(name, real_alias, friendly_name, company_name):
    ret = api.FtVspcCreateTwinPortExA(create_string_buffer(name),
                                      create_string_buffer(real_alias),
                                      create_string_buffer(friendly_name),
                                      create_string_buffer(company_name))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcCreateTwinPortByNum(num, real_alias):
    ret = api.FtVspcCreateTwinPortByNumA(num,
                                         create_string_buffer(real_alias))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcRemovePort(port_name):
    ret = api.FtVspcRemovePortA(create_string_buffer(port_name.encode('utf-8')))
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcRemovePortByNum(port_num):
    ret = api.FtVspcRemovePortByNum(port_num)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcAttach(port_name, event_cb, context):
    ret = api.FtVspcAttachA(create_string_buffer(port_name.encode('utf-8')),
                            event_cb,
                            context)
    if ret == 0:
        print_api_error()
    return ret


def FtVspcAttachByNum(port_num, event_cb, context):
    ret = api.FtVspcAttachByNum(port_num,
                                event_cb,
                                context)
    if ret == 0:
        print_api_error()
    return ret

def FtVspcDetach(port_handle):
    ret = api.FtVspcDetach(port_handle)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcGetPermanent(name):
    permanent = c_uint(0)
    ret = api.FtVspcGetPermanentA(create_string_buffer(name.encode('utf-8')), pointer(permanent))
    if ret == 0:
        print_api_error()
        return None
    return permanent.value != 0


def FtVspcGetPermanentByNum(num):
    permanent = c_uint(0)
    ret = api.FtVspcGetPermanentByNum(num, pointer(permanent))
    if ret == 0:
        print_api_error()
        return None
    return permanent.value != 0


def FtVspcGetPortType(name):
    permanent = c_uint(0)
    ret = api.FtVspcGetPortTypeA(create_string_buffer(name.encode('utf-8')), pointer(permanent))
    if ret == 0:
        print_api_error()
        return None
    return permanent.value != 0


def FtVspcGetPortTypeByNum(num):
    permanent = c_uint(0)
    ret = api.FtVspcGetPortTypeByNum(num, pointer(permanent))
    if ret == 0:
        print_api_error()
        return None
    return permanent != 0


def FtVspcGetQueryOpen(name):
    result = c_uint(0)
    ret = api.FtVspcGetQueryOpenA(create_string_buffer(name.encode('utf-8')), pointer(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetQueryOpenByNum(num):
    result = c_uint(0)
    ret = api.FtVspcGetQueryOpenByNum(num, pointer(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcSetPermanent(name, permanent):
    c_per = c_uint(0)
    if permanent is True:
        c_per = c_uint(1)
    ret = api.FtVspcSetPermanentA(create_string_buffer(name.encode('utf-8')), c_per)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcSetPermanentByNum(num, permanent):
    c_per = c_uint(0)
    if permanent is True:
        c_per = c_uint(1)
    ret = api.FtVspcSetPermanentByNum(num, c_per)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcSetQueryOpen(name, query_open):
    c_open = c_uint(0)
    if query_open is True:
        c_open = c_uint(1)
    ret = api.FtVspcSetQueryOpenA(create_string_buffer(name.encode('utf-8')), c_open)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcSetQueryOpenByNum(num, query_open):
    c_open = c_uint(0)
    if query_open is True:
        c_open = c_uint(1)
    ret = api.FtVspcSetQueryOpenByNum(num, c_open)
    if ret == 0:
        print_api_error()
    return ret != 0


def FtVspcRead(port_handle, len):
    s = create_string_buffer(b'\000' * len)
    ret_len = c_ulong(0)
    ret = api.FtVspcRead(port_handle, s, len, byref(ret_len))
    if ret == 0:
        print_api_error()
        return None
    return s[0:ret_len.value]


def FtVspcWrite(port_handle, data):
    ret = api.FtVspcWrite(port_handle, create_string_buffer(data), len(data))

    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcGetBitrateEmulation(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetBitrateEmulation(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetBreak(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetBreak(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetCts(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetCts(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetDcd(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetDcd(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetDsr(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetDsr(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetFraming(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetFraming(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetInQueueBytes(port_handle):
    result = c_ulong(0)
    ret = api.FtVspcGetInQueueBytes(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value


def FtVspcGetOverrun(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetOverrun(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetParity(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetParity(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result.value != 0


def FtVspcGetRing(port_handle):
    result = c_uint(0)
    ret = api.FtVspcGetRing(port_handle, byref(result))
    if ret == 0:
        print_api_error()
        return None
    return result != 0


def FtVspcSetBitrateEmulation(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetBitrateEmulation(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetBreak(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetBreak(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetCts(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetCts(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetDcd(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetDcd(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetDsr(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetDsr(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetFraming(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetFraming(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetOverrun(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetOverrun(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetParity(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetParity(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcSetRing(port_handle, b_val):
    bval = b_val is True and c_uint(1) or c_uint(0)
    ret = api.FtVspcSetRing(port_handle, bval)
    if ret == 0:
        print_api_error()
        return False
    return True


def FtVspcGetInfo():
    info = FTVSPC_INFO()
    ret = api.FtVspcGetInfoA(pointer(info))
    if ret == 0:
        print_api_error()
        return None
    return info

'''
def FtVspcGetPortInfoByNum(num):
    info = FT_VSPC_PORT()
    ret = api.FtVspcGetPortInfoByNum(num, pointer(info))
    if ret == 0:
        print_api_error()
        return None
    return {
        "unPortNo": info.contents.unPortNo,
        "cPortNameA": str(info.contents.cPortNameA, 'GB2312'),
        "cPortNameW": str(info.contents.cPortNameW, 'GB2312')
    }


def FtVspcGetPortInfo(name):
    info = FT_VSPC_PORT()
    ret = api.FtVspcGetPortInfo(create_string_buffer(name), pointer(info))
    if ret == 0:
        print_api_error()
        return None
    return {
        "unPortNo": info.contents.unPortNo,
        "cPortNameA": str(info.contents.cPortNameA, 'GB2312'),
        "cPortNameW": str(info.contents.cPortNameW, 'GB2312')
    }
'''

