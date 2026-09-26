from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.expense import Expense, EXPENSE_CATEGORIES

expense_bp = Blueprint("expense", __name__, url_prefix="/expense")


@expense_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        date_str = request.form.get("date", "").strip()

        errors = []

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid numeric amount.")

        # Validate category
        if not category:
            errors.append("Please select an expense category.")
        elif category not in EXPENSE_CATEGORIES:
            errors.append("Please choose a valid expense category from the list.")

        # Validate description length
        if description and len(description) > 255:
            errors.append("Description cannot exceed 255 characters.")

        # Validate date
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Please provide a valid date in YYYY-MM-DD format.")
        else:
            expense_date = date.today()

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "add_expense.html",
                categories=EXPENSE_CATEGORIES,
                amount=amount_str,
                selected_category=category,
                description=description,
                date_val=date_str or date.today().isoformat(),
            )

        new_expense = Expense(
            user_id=current_user.id,
            amount=round(amount, 2),
            category=category,
            description=description if description else None,
            date=expense_date,
        )

        db.session.add(new_expense)
        db.session.commit()

        flash(f"Successfully recorded ₹{amount:,.2f} for {category}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template(
        "add_expense.html",
        categories=EXPENSE_CATEGORIES,
        date_val=date.today().isoformat(),
    )
