from datetime import datetime, date, timezone
from app.extensions import db


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship(
        "User",
        backref=db.backref("incomes", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Income {self.source}: ${self.amount}>"
