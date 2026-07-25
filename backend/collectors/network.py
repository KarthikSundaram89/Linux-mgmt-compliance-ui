"""
Network Identity Collector
==========================

Collects network identity: hostname, FQDN, DNS,
interfaces, IP addresses, and default gateway.
Does NOT collect AWS networking metadata.
"""

from typing import Any, Dict, FrozenSet, List

from backend.collectors.base import BaseCollector, LinuxDistro
from backend.ssh.connection import SSHConnection


class NetworkCollector(BaseCollector):
    """Collects network identity and configuration."""

    name = "network"
    version = "1.0.0"
    description = "Collects network identity, DNS, IPs, gateway"
    supported_distros: FrozenSet[LinuxDistro] = frozenset(LinuxDistro)

    async def collect(
        self, connection: SSHConnection, distro: LinuxDistro
    ) -> Dict[str, Any]:
        """Collect network data."""
        data: Dict[str, Any] = {}

        # Hostname
        result = await self.execute_command(connection, "hostname")
        data["hostname"] = result.stdout.strip() if result.exit_code == 0 else ""

        result = await self.execute_command(connection, "hostname -f")
        data["fqdn"] = result.stdout.strip() if result.exit_code == 0 else ""

        # DNS configuration
        result = await self.execute_command(connection, "cat /etc/resolv.conf")
        if result.exit_code == 0:
            dns = self._parse_resolv_conf(result.stdout)
            data["dns_servers"] = dns["nameservers"]
            data["search_domains"] = dns["search"]

        # Default gateway
        result = await self.execute_command(connection, "ip route show")
        if result.exit_code == 0:
            data["default_gateway"] = self._extract_gateway(result.stdout)
            data["routes"] = self._parse_routes(result.stdout)

        # Interfaces and IPs
        result = await self.execute_command(connection, "ip addr show")
        if result.exit_code == 0:
            interfaces = self._parse_ip_addr(result.stdout)
            data["interfaces"] = interfaces
            data["primary_interface"] = self._find_primary(interfaces)

        return data

    def _parse_resolv_conf(self, content: str) -> Dict[str, List[str]]:
        """Parse /etc/resolv.conf."""
        result = {"nameservers": [], "search": []}
        for line in content.strip().splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2:
                    result["nameservers"].append(parts[1])
            elif line.startswith("search") or line.startswith("domain"):
                parts = line.split()
                result["search"].extend(parts[1:])
        return result

    def _extract_gateway(self, content: str) -> str:
        """Extract default gateway from ip route output."""
        for line in content.strip().splitlines():
            if line.startswith("default"):
                parts = line.split()
                if "via" in parts:
                    idx = parts.index("via")
                    return parts[idx + 1] if idx + 1 < len(parts) else ""
        return ""

    def _parse_routes(self, content: str) -> List[Dict[str, str]]:
        """Parse ip route output."""
        routes = []
        for line in content.strip().splitlines():
            parts = line.split()
            if not parts:
                continue
            route = {"destination": parts[0]}
            if "via" in parts:
                idx = parts.index("via")
                route["gateway"] = parts[idx + 1] if idx + 1 < len(parts) else ""
            if "dev" in parts:
                idx = parts.index("dev")
                route["interface"] = parts[idx + 1] if idx + 1 < len(parts) else ""
            routes.append(route)
        return routes

    def _parse_ip_addr(self, content: str) -> List[Dict[str, Any]]:
        """Parse ip addr show output."""
        interfaces: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}

        for line in content.strip().splitlines():
            if line and not line.startswith(" "):
                if current:
                    interfaces.append(current)
                parts = line.split(":")
                iface_name = parts[1].strip() if len(parts) > 1 else ""
                current = {
                    "name": iface_name,
                    "mac_address": "",
                    "ipv4_addresses": [],
                    "ipv6_addresses": [],
                    "state": "",
                }
                if "state" in line:
                    state_parts = line.split("state")
                    if len(state_parts) > 1:
                        current["state"] = state_parts[1].split()[0]
            elif line.strip().startswith("link/ether"):
                parts = line.split()
                if len(parts) >= 2:
                    current["mac_address"] = parts[1]
            elif line.strip().startswith("inet "):
                parts = line.split()
                if len(parts) >= 2:
                    current["ipv4_addresses"].append(parts[1])
            elif line.strip().startswith("inet6"):
                parts = line.split()
                if len(parts) >= 2:
                    current["ipv6_addresses"].append(parts[1])

        if current:
            interfaces.append(current)

        return interfaces

    def _find_primary(self, interfaces: List[Dict]) -> str:
        """Find the primary interface (non-loopback with an IP)."""
        for iface in interfaces:
            name = iface.get("name", "")
            if name == "lo" or name.startswith("docker") or name.startswith("veth"):
                continue
            if iface.get("ipv4_addresses"):
                return name
        return ""
