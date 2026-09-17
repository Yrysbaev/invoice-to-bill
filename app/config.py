"""Application configuration, loaded from environment variables.

Milestone 1: this just reads values from the environment (and a local .env
file, if present). No business logic yet — later milestones use these to talk
to QuickBooks and Anthropic.
"""

import os

from dotenv import load_dotenv

# Load variables from a local .env file if it exists. Real environment
# variables always take precedence over the file.
load_dotenv()


class Config:
    """Base configuration read from environment variables."""

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # QuickBooks Online
    QB_CLIENT_ID = os.environ.get("QB_CLIENT_ID")
    QB_CLIENT_SECRET = os.environ.get("QB_CLIENT_SECRET")
    QB_REDIRECT_URI = os.environ.get("QB_REDIRECT_URI")
    QB_ENVIRONMENT = os.environ.get("QB_ENVIRONMENT", "sandbox")

    # Anthropic (Claude)
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    # Where the OAuth tokens are persisted (git-ignored).
    TOKEN_STORE_PATH = os.environ.get("TOKEN_STORE_PATH", "tokens.json")

    # --- QuickBooks / Intuit OAuth2 endpoints (same for sandbox & production) ---
    QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
    QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    QB_REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
    QB_SCOPE = "com.intuit.quickbooks.accounting"

    @property
    def qb_api_base(self) -> str:
        """Base URL for the Accounting API — differs by environment."""
        if (self.QB_ENVIRONMENT or "sandbox").lower() == "production":
            return "https://quickbooks.api.intuit.com"
        return "https://sandbox-quickbooks.api.intuit.com"

    @property
    def is_quickbooks_configured(self) -> bool:
        return bool(
            self.QB_CLIENT_ID
            and self.QB_CLIENT_SECRET
            and self.QB_REDIRECT_URI
        )

    @property
    def is_anthropic_configured(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)
