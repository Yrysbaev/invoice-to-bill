"""HTTP routes.

Milestone 2: QuickBooks OAuth2 authorization-code flow.
  GET /connect          -> redirect to Intuit consent screen
  GET /callback         -> exchange the auth code for tokens, store them
  POST /disconnect      -> forget the stored tokens
  GET /test-connection  -> call CompanyInfo to prove the token works

Later milestones add PDF upload, review, and Bill submission.
"""

import secrets
from datetime import datetime, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .quickbooks import QuickBooksClient, QuickBooksError
from .token_store import TokenStore

bp = Blueprint("main", __name__)


def _store() -> TokenStore:
    return TokenStore(current_app.config["TOKEN_STORE_PATH"])


def _client() -> QuickBooksClient:
    return QuickBooksClient(current_app.config, _store())


@bp.route("/")
def index():
    cfg = current_app.config
    bundle = _store().load()

    connection = None
    if bundle is not None:
        connection = {
            "realm_id": bundle.realm_id,
            "access_expires": datetime.fromtimestamp(
                bundle.access_expires_at, tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M UTC"),
            "refresh_expired": bundle.refresh_expired(),
        }

    status = {
        "quickbooks_configured": bool(
            cfg.get("QB_CLIENT_ID")
            and cfg.get("QB_CLIENT_SECRET")
            and cfg.get("QB_REDIRECT_URI")
        ),
        "anthropic_configured": bool(cfg.get("ANTHROPIC_API_KEY")),
        "environment": cfg.get("QB_ENVIRONMENT"),
    }
    return render_template("index.html", status=status, connection=connection)


@bp.route("/connect")
def connect():
    cfg = current_app.config
    if not (cfg.get("QB_CLIENT_ID") and cfg.get("QB_CLIENT_SECRET") and cfg.get("QB_REDIRECT_URI")):
        flash("QuickBooks credentials are not configured. Fill in .env first.", "error")
        return redirect(url_for("main.index"))

    # CSRF protection: random state echoed back on the callback.
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    return redirect(_client().authorize_url(state))


@bp.route("/callback")
def callback():
    # Intuit may send an error instead of a code (e.g. user declined).
    error = request.args.get("error")
    if error:
        flash(f"QuickBooks authorization was declined: {error}", "error")
        return redirect(url_for("main.index"))

    state = request.args.get("state")
    expected = session.pop("oauth_state", None)
    if not state or state != expected:
        flash("OAuth state mismatch — please try connecting again.", "error")
        return redirect(url_for("main.index"))

    code = request.args.get("code")
    realm_id = request.args.get("realmId")
    if not code or not realm_id:
        flash("Missing authorization code or realmId from QuickBooks.", "error")
        return redirect(url_for("main.index"))

    try:
        _client().exchange_code(code, realm_id)
    except QuickBooksError as exc:
        flash(str(exc), "error")
        return redirect(url_for("main.index"))

    flash("Connected to QuickBooks.", "success")
    return redirect(url_for("main.index"))


@bp.route("/disconnect", methods=["POST"])
def disconnect():
    _store().clear()
    flash("Disconnected — stored tokens removed.", "success")
    return redirect(url_for("main.index"))


@bp.route("/test-connection")
def test_connection():
    try:
        info = _client().company_info()
        name = info.get("CompanyInfo", {}).get("CompanyName", "(unknown)")
        flash(f"Token works. Connected company: {name}", "success")
    except QuickBooksError as exc:
        flash(str(exc), "error")
    return redirect(url_for("main.index"))


@bp.route("/health")
def health():
    return {"status": "ok"}
