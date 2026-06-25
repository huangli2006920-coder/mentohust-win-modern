from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
from pathlib import Path
import subprocess

from scapy.all import conf
from scapy.arch.windows import get_windows_if_list

from .windows import hidden_subprocess_kwargs


@dataclass(slots=True)
class WindowsInterface:
    index: int
    name: str
    description: str
    guid: str
    network_name: str
    mac: str
    ipv4: str
    nameservers: list[str]


@dataclass(slots=True)
class InterfaceNetworkDetails:
    ipv4: str
    mask: str
    gateway: str
    dns: str


def _first_ipv4(values: list[str]) -> str:
    for item in values:
        try:
            parsed = ipaddress.ip_address(item)
        except ValueError:
            continue
        if parsed.version == 4:
            return str(parsed)
    return "0.0.0.0"


def _prefix_to_mask(prefix_length: int) -> str:
    network = ipaddress.IPv4Network(f"0.0.0.0/{prefix_length}")
    return str(network.netmask)


def list_interfaces() -> list[WindowsInterface]:
    conf.use_pcap = True
    raw_interfaces = get_windows_if_list()
    pcap_map = {
        getattr(iface, "guid", ""): getattr(iface, "network_name", str(iface))
        for iface in conf.ifaces.values()
    }
    results: list[WindowsInterface] = []
    for item in raw_interfaces:
        description = item.get("description", "")
        if not description or "Npcap Packet Driver" in description or "WFP " in description:
            continue
        mac = item.get("mac", "")
        network_name = pcap_map.get(item.get("guid", ""), "")
        if not mac or not network_name:
            continue
        results.append(
            WindowsInterface(
                index=int(item["index"]),
                name=item.get("name", ""),
                description=description,
                guid=item.get("guid", ""),
                network_name=network_name,
                mac=mac,
                ipv4=_first_ipv4(item.get("ips", [])),
                nameservers=[value for value in item.get("nameservers", []) if ":" not in value],
            )
        )
    return results


def find_interface(interface_id: str = "", description: str = "") -> WindowsInterface | None:
    normalized_id = interface_id.strip().lower()
    normalized_description = description.strip().lower()
    for interface in list_interfaces():
        if normalized_id and interface.network_name.lower() == normalized_id:
            return interface
        if normalized_id and interface.guid.lower() == normalized_id:
            return interface
        if normalized_description and interface.description.lower() == normalized_description:
            return interface
        if normalized_description and interface.name.lower() == normalized_description:
            return interface
    return None


def read_network_details(interface: WindowsInterface) -> InterfaceNetworkDetails:
    script = rf"""
$cfg = Get-NetIPConfiguration -InterfaceIndex {interface.index}
$ipv4 = $null
$prefix = $null
if ($cfg.IPv4Address) {{
  $entry = $cfg.IPv4Address | Select-Object -First 1
  $ipv4 = $entry.IPAddress
  $prefix = $entry.PrefixLength
}}
$gateway = $null
if ($cfg.IPv4DefaultGateway) {{
  $gateway = ($cfg.IPv4DefaultGateway | Select-Object -First 1).NextHop
}}
$dns = @()
if ($cfg.DnsServer) {{
  $dns = $cfg.DnsServer.ServerAddresses
}}
[pscustomobject]@{{
  IPv4Address = $ipv4
  PrefixLength = $prefix
  IPv4DefaultGateway = $gateway
  DnsServers = $dns
}} | ConvertTo-Json -Compress -Depth 3
"""
    output = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        **hidden_subprocess_kwargs(),
    )
    payload = {}
    if output.returncode == 0 and output.stdout.strip():
        payload = json.loads(output.stdout)

    ipv4 = payload.get("IPv4Address") or interface.ipv4 or "0.0.0.0"
    prefix = payload.get("PrefixLength")
    mask = _prefix_to_mask(int(prefix)) if prefix is not None else "255.255.255.0"
    gateway = payload.get("IPv4DefaultGateway") or "0.0.0.0"
    dns_servers = payload.get("DnsServers") or interface.nameservers
    dns = dns_servers[0] if dns_servers else "0.0.0.0"
    return InterfaceNetworkDetails(ipv4=ipv4, mask=mask, gateway=gateway, dns=dns)


def has_active_wifi_connection() -> bool:
    script = r"""
$adapters = Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object {
  $_.Status -eq 'Up' -and (
    $_.NdisPhysicalMedium -eq 'Native 802.11' -or
    $_.Name -match 'wi-?fi|wlan' -or
    $_.InterfaceDescription -match 'wireless|wi-?fi|802\.11'
  )
}
[bool]($adapters | Select-Object -First 1)
"""
    output = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", script],
        check=False,
        capture_output=True,
        text=True,
        **hidden_subprocess_kwargs(),
    )
    return output.returncode == 0 and output.stdout.strip().lower() == "true"
