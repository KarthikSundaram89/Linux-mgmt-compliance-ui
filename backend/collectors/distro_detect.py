"""
Distribution Detection
======================

Detects the Linux distribution of a remote server
by parsing /etc/os-release and related files.
"""

import logging
from typing import Tuple

from backend.collectors.base import LinuxDistro
from backend.ssh.connection import CommandResult, SSHConnection

logger = logging.getLogger("collector")

# Mapping of os-release ID values to our enum
_DISTRO_MAP = {
    "rhel": LinuxDistro.RHEL,
    "redhat": LinuxDistro.RHEL,
    "amzn": LinuxDistro.AMAZON_LINUX,
    "amazon": LinuxDistro.AMAZON_LINUX,
    "ubuntu": LinuxDistro.UBUNTU,
    "debian": LinuxDistro.DEBIAN,
    "rocky": LinuxDistro.ROCKY,
    "ol": LinuxDistro.ORACLE,
    "oracle": LinuxDistro.ORACLE,
    "kali": LinuxDistro.KALI,
    "centos": LinuxDistro.CENTOS,
    "sles": LinuxDistro.SUSE,
    "suse": LinuxDistro.SUSE,
    "opensuse": LinuxDistro.SUSE,
    "opensuse-leap": LinuxDistro.SUSE,
    "opensuse-tumbleweed": LinuxDistro.SUSE,
}


async def detect_distribution(
    connection: SSHConnection,
) -> Tuple[LinuxDistro, str, str]:
    """
    Detect the Linux distribution of a remote server.

    Reads /etc/os-release to determine the distribution family,
    version, and pretty name.

    Args:
        connection: Active SSH connection.

    Returns:
        Tuple of (LinuxDistro enum, version string, pretty name).
    """
    result = await connection.execute("cat /etc/os-release")

    if result.exit_code != 0:
        logger.warning("Could not read /etc/os-release")
        return LinuxDistro.UNKNOWN, "", ""

    os_release = _parse_os_release(result.stdout)

    distro_id = os_release.get("ID", "").lower().strip('"')
    version = os_release.get("VERSION_ID", "").strip('"')
    pretty_name = os_release.get("PRETTY_NAME", "").strip('"')

    # Handle ID_LIKE for derivative distributions
    id_like = os_release.get("ID_LIKE", "").lower().strip('"')

    # Direct match
    distro = _DISTRO_MAP.get(distro_id, None)

    # Fallback to ID_LIKE
    if distro is None and id_like:
        for like_id in id_like.split():
            distro = _DISTRO_MAP.get(like_id, None)
            if distro:
                break

    if distro is None:
        distro = LinuxDistro.UNKNOWN
        logger.warning(
            f"Unknown distribution: ID={distro_id}, ID_LIKE={id_like}"
        )

    logger.info(
        f"Detected distribution: {distro.value}",
        extra={
            "distro": distro.value,
            "version": version,
            "pretty_name": pretty_name,
        },
    )

    return distro, version, pretty_name


def _parse_os_release(content: str) -> dict:
    """Parse /etc/os-release into a dictionary."""
    data = {}
    for line in content.strip().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"')
    return data
