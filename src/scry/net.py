"""Network safety — an SSRF guard for the generic fetchers.

Refuses to fetch non-public addresses (private / loopback / link-local / reserved / metadata),
allows only http(s), and re-validates every redirect hop. Tuned anti-bot / proxy behavior is not
part of this core.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit


def _blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def assert_public_url(url: str) -> None:
    """Raise ValueError unless `url` is http(s) and resolves only to public IP addresses.

    Resolving the host (rather than trusting the literal) blocks DNS-rebinding to internal hosts and
    cloud-metadata endpoints (169.254.169.254 is link-local → blocked).
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError(f"refusing non-http(s) URL: {parts.scheme or url!r}")
    host = parts.hostname
    if not host:
        raise ValueError(f"URL has no host: {url!r}")
    try:
        infos = socket.getaddrinfo(
            host, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise ValueError(f"cannot resolve host: {host}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _blocked(ip):
            raise ValueError(f"refusing non-public address for {host}: {ip}")


def safe_get(client, url: str, *, headers: dict | None = None, max_redirects: int = 5):
    """httpx GET that validates the URL and every redirect hop with `assert_public_url`.

    Use instead of `client.get(url, follow_redirects=True)`, which would follow a redirect to an
    internal address unchecked.
    """
    current = url
    for _ in range(max_redirects + 1):
        assert_public_url(current)
        resp = client.get(current, headers=headers, follow_redirects=False)
        if resp.is_redirect and (loc := resp.headers.get("location")):
            current = urljoin(current, loc)
            continue
        return resp
    raise ValueError(f"too many redirects from {url!r}")
