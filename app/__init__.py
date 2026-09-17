"""Flask application factory.

Milestone 1: creates the app, loads config, and registers the (currently
minimal) routes. No QuickBooks or Claude wiring yet.
"""

from flask import Flask

from .config import Config


def create_app(config_object: Config | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config())

    from .routes import bp as main_bp

    app.register_blueprint(main_bp)

    return app
