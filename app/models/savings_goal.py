from datetime import datetime, timezone
from app.extensions import db


class SavingsGoal(db.Model):
    __tablename__ = "savings_goal"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    goal_name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
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

    user = db.relationship(
        "User",
        backref=db.backref("savings_goals", lazy=True, cascade="all, delete-orphan"),
    )

    @property
    def remaining_amount(self):
        return max(0.0, round(self.target_amount - self.current_amount, 2))

    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 0.0
        return round((self.current_amount / self.target_amount) * 100.0, 1)

    @property
    def progress_bar_width(self):
        return min(100.0, max(0.0, self.progress_percentage))

    @property
    def is_completed(self):
        return self.current_amount >= self.target_amount

    def __repr__(self):
        return f"<SavingsGoal {self.goal_name}: ₹{self.current_amount}/₹{self.target_amount}>"
