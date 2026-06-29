"""SSRF guard — assert_public_url must block internal/invalid targets."""

import pytest

from scry.net import assert_public_url

BLOCKED = [
    "http://127.0.0.1/",                              # loopback
    "http://169.254.169.254/latest/meta-data/",      # cloud metadata (link-local)
    "http://10.1.2.3/",                               # private
    "http://192.168.0.5/",                            # private
    "http://[::1]/",                                  # loopback v6
    "http://0.0.0.0/",                                # unspecified
    "ftp://host/x",                                   # non-http scheme
    "file:///etc/passwd",                            # non-http scheme
    "http:///nohost",                                 # no host
]


@pytest.mark.parametrize("url", BLOCKED)
def test_blocks_internal_and_invalid(url):
    with pytest.raises(ValueError):
        assert_public_url(url)
