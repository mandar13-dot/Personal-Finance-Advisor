import os

from flask import Flask
from dotenv import load_dotenv

from app.extensions import db, login_manager

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    default_db_path = os.path.join(
        app.instance_path,
        "finance.db"
    )

    raw_database_uri = os.getenv("DATABASE_URL")
    database_uri = raw_database_uri.strip() if raw_database_uri else ""

    # Treat empty, whitespace-only, or invalid non-URL values as missing
    if not database_uri or "://" not in database_uri:
        database_uri = f"sqlite:///{default_db_path}"

    app.config.from_mapping(
        SECRET_KEY=os.getenv(
            "SECRET_KEY",
            "dev-secret-key-change-in-production"
        ),
        SQLALCHEMY_DATABASE_URI=database_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    # Initialize extensions
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Template filters
    @app.template_filter("nl2br")
    def nl2br_filter(s):
        if not s:
            return ""
        from markupsafe import Markup, escape
        return Markup("<br>".join(escape(s).splitlines()))

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User

        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Import models so SQLAlchemy knows about them
    from app.models import User, Income, Expense, Budget, SavingsGoal

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.income import income_bp
    from app.routes.expense import expense_bp
    from app.routes.budget import budget_bp
    from app.routes.goals import goals_bp
    from app.routes.reports import reports_bp
    from app.routes.advisor import advisor_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(advisor_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app