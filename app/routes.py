"""HTTP routes.

Milestone 1: only a landing page and a small health check. Later milestones add
/connect, /callback, upload, review, and submit routes.
"""

from flask import Blueprint, current_app, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    cfg = current_app.config
    status = {
        "quickbooks_configured": bool(
            cfg.get("QB_CLIENT_ID")
            and cfg.get("QB_CLIENT_SECRET")
            and cfg.get("QB_REDIRECT_URI")
        ),
        "anthropic_configured": bool(cfg.get("ANTHROPIC_API_KEY")),
        "environment": cfg.get("QB_ENVIRONMENT"),
    }
    return render_template("index.html", status=status)


@bp.route("/health")
def health():
    return {"status": "ok"}
