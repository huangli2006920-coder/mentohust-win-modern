from __future__ import annotations

import ctypes
import subprocess
import sys


APP_TITLE = "MentoHUST Win Modern"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def build_relaunch_parameters(argv: list[str] | None = None, *, frozen: bool | None = None) -> str:
    use_frozen = is_frozen() if frozen is None else frozen
    args = list(argv or [])
    if not use_frozen:
        args = ["-m", "mentohust_modern", *args]
    return subprocess.list2cmdline(args)


def ensure_admin() -> bool:
    if is_admin():
        return False
    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        build_relaunch_parameters(sys.argv[1:]),
        None,
        1,
    )
    if result <= 32:
        ctypes.windll.user32.MessageBoxW(
            None,
            "MentoHUST Win Modern 需要管理员权限，才能更稳定地访问 Npcap 和原始网卡。",
            APP_TITLE,
            0x10,
        )
        raise SystemExit(1)
    return True
