from datetime import datetime, date, timezone
from app.extensions import db

EXPENSE_CATEGORIES = [
    "Food",
    "Rent",
    "Transport",
    "Entertainment",
    "Shopping",
    "Utilities",
    "Education",
    "Healthcare",
    "Other",
]


class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship(
        "User",
        backref=db.backref("expenses", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Expense {self.category}: ₹{self.amount}>"
