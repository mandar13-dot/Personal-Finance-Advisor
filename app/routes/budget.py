from datetime import datetime, date, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.budget import Budget

budget_bp = Blueprint("budget", __name__, url_prefix="/budget")


@budget_bp.route("/", methods=["GET", "POST"])
@budget_bp.route("/set", methods=["GET", "POST"])
@login_required
def manage_budget():
    today = date.today()
    default_month = today.strftime("%Y-%m")

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        month_str = request.form.get("month", "").strip()

        errors = []

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Budget amount must be a positive number greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid numeric budget amount.")

        # Validate month
        if not month_str:
            errors.append("Please select a month.")
        else:
            try:
                parsed_month = datetime.strptime(month_str, "%Y-%m")
            except (ValueError, TypeError):
                errors.append("Please provide a valid month in YYYY-MM format.")

        if errors:
            for error in errors:
                flash(error, "danger")
            all_budgets = (
                Budget.query.filter_by(user_id=current_user.id)
                .order_by(Budget.month.desc())
                .all()
            )
            return render_template(
                "budget.html",
                selected_month=month_str or default_month,
                amount=amount_str,
                existing_budget=None,
                all_budgets=all_budgets,
            )

        formatted_month_name = parsed_month.strftime("%B %Y")

        # Check if budget already exists for this user and month
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            month=month_str,
        ).first()

        if budget:
            budget.amount = round(amount, 2)
            budget.updated_at = datetime.now(timezone.utc)
            action_text = "updated"
        else:
            budget = Budget(
                user_id=current_user.id,
                amount=round(amount, 2),
                month=month_str,
            )
            db.session.add(budget)
            action_text = "set"

        db.session.commit()

        flash(
            f"Successfully {action_text} budget of ₹{amount:,.2f} for {formatted_month_name}!",
            "success",
        )
        return redirect(url_for("main.dashboard"))

    # GET request
    selected_month = request.args.get("month", default_month).strip()
    try:
        datetime.strptime(selected_month, "%Y-%m")
    except (ValueError, TypeError):
        selected_month = default_month

    existing_budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=selected_month,
    ).first()

    all_budgets = (
        Budget.query.filter_by(user_id=current_user.id)
        .order_by(Budget.month.desc())
        .all()
    )

    return render_template(
        "budget.html",
        selected_month=selected_month,
        existing_budget=existing_budget,
        all_budgets=all_budgets,
    )
