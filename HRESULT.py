##contains HRESULTs for the DirectShow and DexterLib interfaces's functions
from ctypes import c_long
buffer_hresult={
    "E_INVALIDARG":c_long(0x80070057).value,
    "E_OUTOFMEMORY":c_long(0x8007000E).value,
    "E_POINTER":c_long(0x80004003).value,
    "S_OK":c_long(0x00000000).value,
    "VFW_E_NOT_CONNECTED":c_long(0x80040209).value,
    "VFW_E_WRONG_STATE": c_long(0x80040227).value,
}
buffer_error_hresult={
    "E_INVALIDARG":c_long(0x80070057).value,
    "E_OUTOFMEMORY":c_long(0x8007000E).value,
    "E_POINTER":c_long(0x80004003).value,
    "VFW_E_NOT_CONNECTED":c_long(0x80040209).value,
    "VFW_E_WRONG_STATE": c_long(0x80040227).value,
}
