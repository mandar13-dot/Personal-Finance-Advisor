from datetime import datetime, timezone
from app.extensions import db


class Budget(db.Model):
    __tablename__ = "budget"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Float, nullable=False)
    # Stored as 'YYYY-MM' e.g. '2026-09'
    month = db.Column(db.String(7), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "month", name="uq_user_budget_month"),
    )

    user = db.relationship(
        "User",
        backref=db.backref("budgets", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Budget {self.month}: ₹{self.amount}>"
