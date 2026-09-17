"""QuickBooks Online OAuth2 client (authorization-code flow).

Milestone 2 scope:
  * build the Intuit consent URL   -> authorize_url()
  * exchange an auth code for tokens -> exchange_code()
  * refresh an expired access token  -> refresh()
  * a helper that always returns a valid access token, refreshing if needed
  * a tiny CompanyInfo call to prove the stored token works

Token persistence lives in :mod:`app.token_store`.
"""

from __future__ import annotations

import base64
import time
from urllib.parse import urlencode

import requests

from .token_store import TokenBundle, TokenStore

# QuickBooks refresh tokens last a while but are not returned with an explicit
# absolute expiry we can rely on across refreshes, so fall back to this when the
# response omits x_refresh_token_expires_in.
_DEFAULT_REFRESH_TTL = 100 * 24 * 60 * 60  # ~100 days, in seconds


class QuickBooksError(RuntimeError):
    """Raised when a QuickBooks OAuth or API call fails."""


class QuickBooksClient:
    def __init__(self, config, store: TokenStore):
        self.cfg = config
        self.store = store

    # --- helpers -----------------------------------------------------------

    def _api_base(self) -> str:
        """Accounting API base URL — differs by environment."""
        env = (self.cfg.get("QB_ENVIRONMENT") or "sandbox").lower()
        if env == "production":
            return "https://quickbooks.api.intuit.com"
        return "https://sandbox-quickbooks.api.intuit.com"

    def _basic_auth_header(self) -> str:
        raw = f"{self.cfg['QB_CLIENT_ID']}:{self.cfg['QB_CLIENT_SECRET']}"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return f"Basic {encoded}"

    def _bundle_from_token_response(self, data: dict, realm_id: str) -> TokenBundle:
        now = time.time()
        access_ttl = int(data.get("expires_in", 3600))
        refresh_ttl = int(data.get("x_refresh_token_expires_in", _DEFAULT_REFRESH_TTL))
        return TokenBundle(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            realm_id=realm_id,
            access_expires_at=now + access_ttl,
            refresh_expires_at=now + refresh_ttl,
        )

    # --- OAuth flow --------------------------------------------------------

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.cfg["QB_CLIENT_ID"],
            "response_type": "code",
            "scope": self.cfg["QB_SCOPE"],
            "redirect_uri": self.cfg["QB_REDIRECT_URI"],
            "state": state,
        }
        return f"{self.cfg['QB_AUTH_URL']}?{urlencode(params)}"

    def exchange_code(self, code: str, realm_id: str) -> TokenBundle:
        resp = requests.post(
            self.cfg["QB_TOKEN_URL"],
            headers={
                "Authorization": self._basic_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.cfg["QB_REDIRECT_URI"],
            },
            timeout=30,
        )
        if not resp.ok:
            raise QuickBooksError(
                f"Token exchange failed ({resp.status_code}): {resp.text}"
            )
        bundle = self._bundle_from_token_response(resp.json(), realm_id)
        self.store.save(bundle)
        return bundle

    def refresh(self, bundle: TokenBundle) -> TokenBundle:
        if bundle.refresh_expired():
            raise QuickBooksError(
                "Refresh token has expired — reconnect to QuickBooks."
            )
        resp = requests.post(
            self.cfg["QB_TOKEN_URL"],
            headers={
                "Authorization": self._basic_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": bundle.refresh_token,
            },
            timeout=30,
        )
        if not resp.ok:
            raise QuickBooksError(
                f"Token refresh failed ({resp.status_code}): {resp.text}"
            )
        new_bundle = self._bundle_from_token_response(resp.json(), bundle.realm_id)
        self.store.save(new_bundle)
        return new_bundle

    def valid_bundle(self) -> TokenBundle:
        """Return a stored bundle with a fresh access token, refreshing if needed."""
        bundle = self.store.load()
        if bundle is None:
            raise QuickBooksError("Not connected to QuickBooks.")
        if bundle.access_expired():
            bundle = self.refresh(bundle)
        return bundle

    # --- a minimal authenticated API call to prove the token works ---------

    def company_info(self) -> dict:
        bundle = self.valid_bundle()
        url = (
            f"{self._api_base()}/v3/company/{bundle.realm_id}"
            f"/companyinfo/{bundle.realm_id}"
        )
        resp = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {bundle.access_token}",
                "Accept": "application/json",
            },
            params={"minorversion": "73"},
            timeout=30,
        )
        if not resp.ok:
            raise QuickBooksError(
                f"CompanyInfo call failed ({resp.status_code}): {resp.text}"
            )
        return resp.json()
