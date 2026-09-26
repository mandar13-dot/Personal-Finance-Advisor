from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.income import Income

income_bp = Blueprint("income", __name__, url_prefix="/income")


@income_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        source = request.form.get("source", "").strip()
        date_str = request.form.get("date", "").strip()

        errors = []

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid numeric amount.")

        # Validate source
        if not source:
            errors.append("Income source cannot be empty.")
        elif len(source) > 100:
            errors.append("Income source cannot exceed 100 characters.")

        # Validate date
        if date_str:
            try:
                income_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Please provide a valid date in YYYY-MM-DD format.")
        else:
            income_date = date.today()

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "add_income.html",
                amount=amount_str,
                source=source,
                date_val=date_str or date.today().isoformat(),
            )

        new_income = Income(
            user_id=current_user.id,
            amount=round(amount, 2),
            source=source,
            date=income_date,
        )

        db.session.add(new_income)
        db.session.commit()

        flash(f"Successfully recorded ₹{amount:,.2f} from {source}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_income.html", date_val=date.today().isoformat())
