from __future__ import annotations

from pathlib import Path
import re

from .config import MentohustConfig


OPTION_RE = re.compile(r"^\s*option\s+(\S+)\s+'(.*)'\s*$")


def load_openwrt_config_text(text: str) -> MentohustConfig:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = OPTION_RE.match(line)
        if match:
            values[match.group(1)] = match.group(2)

    config = MentohustConfig()
    config.enable = values.get("enable", "1") == "1"
    config.username = values.get("username", "")
    config.password = values.get("password", "")
    config.interface_description = values.get("interface", "")
    config.ipaddr = values.get("ipaddr", config.ipaddr)
    config.gateway = values.get("gateway", config.gateway)
    config.mask = values.get("mask", config.mask)
    config.ping = values.get("ping", config.ping)
    config.timeout = int(values.get("timeout", config.timeout))
    config.interval = int(values.get("interval", config.interval))
    config.wait = int(values.get("wait", config.wait))
    config.fail_number = int(values.get("fail_number", config.fail_number))
    config.multicast_address = int(values.get("multicast_address", config.multicast_address))
    config.dhcp_mode = int(values.get("dhcp_mode", config.dhcp_mode))
    config.dhcp_script = values.get("dhcp_script", config.dhcp_script)
    config.version = values.get("version", config.version)
    config.dns = values.get("dns", config.dns)
    return config


def load_openwrt_config_file(path: str | Path) -> MentohustConfig:
    return load_openwrt_config_text(Path(path).read_text(encoding="utf-8"))

