"""Authenticated acquisition — the public contract.

`AuthenticatedFetcher` is the seam between Scry's public core and private site
adapters that need a logged-in session. The core ships only this interface; the
real adapters (login flows, site selectors, anti-bot) live privately and never
appear in scry-core.

Every adapter declares a ``tos_class`` describing how its bytes were obtained, so
downstream consumers — for example a hosted product that must not surface
restricted captures — can gate on it mechanically rather than by memory.

This module is deliberately site-agnostic: no credentials, no selectors, no
evasion logic, no platform names.
"""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

from scry.fetchers import Fetcher
from scry.models import ToSClass


class AuthenticatedFetcher(Fetcher):
    """Fetch a URL using a caller-supplied authenticated context.

    The public core provides only this contract. A concrete (private) adapter
    supplies the authenticated context and declares its ``tos_class``. No
    credentials, selectors, or anti-bot logic belong here or anywhere in scry-core.
    """

    #: Safe default is the most restrictive class; adapters override explicitly.
    tos_class: ToSClass = ToSClass.RESTRICTED_INTERNAL

    @abstractmethod
    def ensure_auth_state(self, path: str | Path, *, force: bool = False) -> Path:
        """Ensure a usable authenticated-session artifact exists at ``path``.

        Generic, site-agnostic gate: return the path if a valid session artifact is
        present; otherwise raise an actionable error telling the caller how to create
        one. ``force`` requests a refresh. The session artifact is a secret — adapters
        must never log, commit, or ship it.
        """

    @abstractmethod
    def authenticated_context(self):
        """Return a context manager yielding an authenticated page/context.

        Adapter-provided. The core never inspects what's inside it.
        """
