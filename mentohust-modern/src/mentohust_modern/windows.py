from __future__ import annotations

import ctypes
import os
from pathlib import Path
import subprocess
from ctypes import wintypes


APP_USER_MODEL_ID = "MentoHUSTWinModern.App"


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
