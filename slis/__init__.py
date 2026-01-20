"""SLIS package.

Keep this module import-light so CLI/scripts (e.g. init_db) can run
without requiring Flask and its extensions to be installed.
"""


def create_app(config_class=None):
    # Lazy imports to avoid hard dependency when running scripts.
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from config import DevConfig
    from datetime import timezone
    try:
        from zoneinfo import ZoneInfo  # py>=3.9
    except Exception:  # pragma: no cover
        ZoneInfo = None

    if config_class is None:
        config_class = DevConfig

    app = Flask(__name__)
    app.config.from_object(config_class)

    db = SQLAlchemy()
    db.init_app(app)

    # Register blueprints
    from slis.routes.transactions import transactions_bp
    from slis.routes.sanctions import sanctions_bp
    from slis.routes.screening import screening_bp
    from slis.routes.web import web_bp


    app.register_blueprint(transactions_bp, url_prefix="/api/batches")
    app.register_blueprint(sanctions_bp, url_prefix="/api/sanctions")
    app.register_blueprint(screening_bp, url_prefix='/api/screening')
    
    app.register_blueprint(web_bp)

    # Minimal additive schema upgrades (no Alembic in this repo).
    try:
        from slis.schema import ensure_schema

        ensure_schema()
    except Exception:
        # Never block app startup on best-effort schema checks.
        pass

    def _to_wib(dt):
        if not dt:
            return None
        try:
            # Assume naive timestamps are stored as UTC.
            if getattr(dt, "tzinfo", None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if ZoneInfo is None:
                return dt
            return dt.astimezone(ZoneInfo("Asia/Jakarta"))
        except Exception:
            return dt

    @app.template_filter("wib")
    def wib(dt):
        """Convert a datetime to WIB (Asia/Jakarta)."""
        return _to_wib(dt)

    @app.template_filter("wib_fmt")
    def wib_fmt(dt, fmt: str = "%Y-%m-%d %H:%M"):
        """Format a datetime in WIB."""
        d = _to_wib(dt)
        if not d:
            return "-"
        try:
            return d.strftime(fmt)
        except Exception:
            return str(d)

    return app
