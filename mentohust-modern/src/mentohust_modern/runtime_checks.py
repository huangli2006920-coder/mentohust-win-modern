from __future__ import annotations

from pathlib import Path

from .config import MentohustConfig


def npcap_installed() -> bool:
    candidates = [
        Path(r"C:\Windows\System32\Npcap\wpcap.dll"),
        Path(r"C:\Windows\SysWOW64\Npcap\wpcap.dll"),
        Path(r"C:\Program Files\Npcap\wpcap.dll"),
    ]
    return any(path.exists() for path in candidates)


def validation_errors(config: MentohustConfig) -> list[str]:
    errors: list[str] = []
    if not npcap_installed():
        errors.append("未检测到 Npcap，请先安装 Npcap 再尝试连接。")
    if not config.client_exe_path().exists():
        errors.append(f"找不到官方客户端文件: {config.client_exe_path()}")
    if not config.username.strip():
        errors.append("用户名不能为空。")
    if not config.password:
        errors.append("密码不能为空。")
    return errors
