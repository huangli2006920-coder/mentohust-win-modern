from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess
import threading
from collections.abc import Callable
from ctypes import wintypes


APP_USER_MODEL_ID = "MentoHUSTWinModern.App"
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
WS_POPUP = 0x80000000


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


class LOGFONTW(ctypes.Structure):
    _fields_ = [
        ("lfHeight", wintypes.LONG),
        ("lfWidth", wintypes.LONG),
        ("lfEscapement", wintypes.LONG),
        ("lfOrientation", wintypes.LONG),
        ("lfWeight", wintypes.LONG),
        ("lfItalic", wintypes.BYTE),
        ("lfUnderline", wintypes.BYTE),
        ("lfStrikeOut", wintypes.BYTE),
        ("lfCharSet", wintypes.BYTE),
        ("lfOutPrecision", wintypes.BYTE),
        ("lfClipPrecision", wintypes.BYTE),
        ("lfQuality", wintypes.BYTE),
        ("lfPitchAndFamily", wintypes.BYTE),
        ("lfFaceName", wintypes.WCHAR * 32),
    ]


class NONCLIENTMETRICSW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("iBorderWidth", ctypes.c_int),
        ("iScrollWidth", ctypes.c_int),
        ("iScrollHeight", ctypes.c_int),
        ("iCaptionWidth", ctypes.c_int),
        ("iCaptionHeight", ctypes.c_int),
        ("lfCaptionFont", LOGFONTW),
        ("iSmCaptionWidth", ctypes.c_int),
        ("iSmCaptionHeight", ctypes.c_int),
        ("lfSmCaptionFont", LOGFONTW),
        ("iMenuWidth", ctypes.c_int),
        ("iMenuHeight", ctypes.c_int),
        ("lfMenuFont", LOGFONTW),
        ("lfStatusFont", LOGFONTW),
        ("lfMessageFont", LOGFONTW),
        ("iPaddedBorderWidth", ctypes.c_int),
    ]


def hidden_subprocess_kwargs() -> dict[str, object]:
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }


def enable_high_dpi_awareness() -> None:
    if os.name != "nt":
        return
    user32 = ctypes.windll.user32
    awareness_contexts = (-4, -3)
    for context in awareness_contexts:
        try:
            if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(context)):
                return
        except Exception:
            break
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def get_system_ui_font() -> tuple[str, int]:
    if os.name != "nt":
        return ("TkDefaultFont", 10)
    spi_getnonclientmetrics = 0x0029
    metrics = NONCLIENTMETRICSW()
    metrics.cbSize = ctypes.sizeof(NONCLIENTMETRICSW)
    try:
        success = ctypes.windll.user32.SystemParametersInfoW(
            spi_getnonclientmetrics,
            metrics.cbSize,
            ctypes.byref(metrics),
            0,
        )
        if success:
            height = metrics.lfMessageFont.lfHeight
            size = max(9, abs(int(height)) * 72 // 96)
            return (metrics.lfMessageFont.lfFaceName, size)
    except Exception:
        pass
    return ("Microsoft YaHei UI", 10)


def set_current_process_app_id(app_id: str = APP_USER_MODEL_ID) -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def apply_window_icons(hwnd: int, icon_path: str | Path) -> list[int]:
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32
    image_icon = 1
    lr_loadfromfile = 0x0010
    wm_seticon = 0x0080
    icon_small = 0
    icon_big = 1
    handles: list[int] = []
    for size, icon_kind in ((16, icon_small), (32, icon_big)):
        handle = user32.LoadImageW(None, str(icon_path), image_icon, size, size, lr_loadfromfile)
        if handle:
            user32.SendMessageW(hwnd, wm_seticon, icon_kind, handle)
            handles.append(handle)
    return handles


def destroy_icon_handles(handles: list[int]) -> None:
    if os.name != "nt":
        return
    user32 = ctypes.windll.user32
    for handle in handles:
        try:
            user32.DestroyIcon(handle)
        except Exception:
            pass


class SessionEndNotifier:
    """用独立隐藏窗口接收关机消息，避免干预 Tk 的窗口过程。"""

    def __init__(self, *, is_connected: Callable[[], bool], on_session_end: Callable[[], None]) -> None:
        self.is_connected = is_connected
        self.on_session_end = on_session_end
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._hwnd = 0
        self._window_proc = None

    def start(self) -> bool:
        if os.name != "nt":
            return False
        self._thread = threading.Thread(target=self._run, daemon=True, name="SessionEndNotifier")
        self._thread.start()
        return self._ready.wait(timeout=2) and bool(self._hwnd)

    def stop(self) -> None:
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        class_name = f"MentoHUSTSessionEndNotifier{ id(self) }"
        wndproc_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = ctypes.c_ushort
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = ctypes.c_int
        user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
        user32.DispatchMessageW.restype = ctypes.c_ssize_t
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.ShutdownBlockReasonCreate.restype = wintypes.BOOL
        user32.ShutdownBlockReasonDestroy.restype = wintypes.BOOL

        @wndproc_type
        def window_proc(hwnd: int, message: int, wparam: int, lparam: int) -> int:
            if message == WM_QUERYENDSESSION:
                if self.is_connected():
                    # 只在确有认证会话时登记原因，避免无意义地影响关机流程。
                    user32.ShutdownBlockReasonCreate(hwnd, "正在断开校园网连接，请不要强行关机。")
                return 1
            if message == WM_ENDSESSION:
                if wparam:
                    try:
                        self.on_session_end()
                    finally:
                        user32.ShutdownBlockReasonDestroy(hwnd)
                return 0
            if message == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if message == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        self._window_proc = window_proc
        instance = kernel32.GetModuleHandleW(None)
        window_class = WNDCLASSW(
            lpfnWndProc=ctypes.cast(window_proc, ctypes.c_void_p).value,
            hInstance=instance,
            lpszClassName=class_name,
        )
        if not user32.RegisterClassW(ctypes.byref(window_class)):
            self._ready.set()
            return
        self._hwnd = user32.CreateWindowExW(
            0, class_name, class_name, WS_POPUP, 0, 0, 0, 0, None, None, instance, None
        )
        self._ready.set()
        if not self._hwnd:
            return
        message = MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
