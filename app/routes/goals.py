from datetime import datetime, date, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models.savings_goal import SavingsGoal

goals_bp = Blueprint("goals", __name__, url_prefix="/goals")


@goals_bp.route("/", methods=["GET"])
@login_required
def list_goals():
    goals = (
        SavingsGoal.query.filter_by(user_id=current_user.id)
        .order_by(SavingsGoal.created_at.desc())
        .all()
    )

    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    total_remaining = sum(g.remaining_amount for g in goals)
    overall_progress = round((total_saved / total_target) * 100, 1) if total_target > 0 else 0.0

    return render_template(
        "goals.html",
        goals=goals,
        total_target=total_target,
        total_saved=total_saved,
        total_remaining=total_remaining,
        overall_progress=overall_progress,
        today=date.today().isoformat(),
    )


@goals_bp.route("/create", methods=["POST"])
@login_required
def create_goal():
    goal_name = request.form.get("goal_name", "").strip()
    target_amount_str = request.form.get("target_amount", "").strip()
    current_amount_str = request.form.get("current_amount", "0").strip() or "0"
    target_date_str = request.form.get("target_date", "").strip()

    errors = []

    if not goal_name:
        errors.append("Goal name cannot be empty.")
    elif len(goal_name) > 100:
        errors.append("Goal name cannot exceed 100 characters.")

    try:
        target_amount = float(target_amount_str)
        if target_amount <= 0:
            errors.append("Target amount must be a positive number greater than 0.")
    except (ValueError, TypeError):
        errors.append("Please enter a valid numeric target amount.")

    try:
        current_amount = float(current_amount_str)
        if current_amount < 0:
            errors.append("Current saved amount cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Please enter a valid numeric current amount.")

    target_date = None
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Please provide a valid target date in YYYY-MM-DD format.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for("goals.list_goals"))

    new_goal = SavingsGoal(
        user_id=current_user.id,
        goal_name=goal_name,
        target_amount=round(target_amount, 2),
        current_amount=round(current_amount, 2),
        target_date=target_date,
    )

    db.session.add(new_goal)
    db.session.commit()

    flash(f"Successfully created savings goal: {goal_name}!", "success")
    return redirect(url_for("goals.list_goals"))


@goals_bp.route("/<int:goal_id>/add-funds", methods=["POST"])
@login_required
def add_funds(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    deposit_str = request.form.get("amount", "").strip()

    try:
        deposit = float(deposit_str)
        if deposit <= 0:
            flash("Deposit amount must be greater than 0.", "danger")
            return redirect(url_for("goals.list_goals"))
    except (ValueError, TypeError):
        flash("Please enter a valid numeric deposit amount.", "danger")
        return redirect(url_for("goals.list_goals"))

    goal.current_amount = round(goal.current_amount + deposit, 2)
    goal.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    if goal.is_completed:
        flash(f"Congratulations! You reached your goal for {goal.goal_name} with ₹{goal.current_amount:,.2f} saved!", "success")
    else:
        flash(f"Added ₹{deposit:,.2f} to {goal.goal_name}! Progress: {goal.progress_percentage}%.", "success")

    return redirect(url_for("goals.list_goals"))


@goals_bp.route("/<int:goal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        goal_name = request.form.get("goal_name", "").strip()
        target_amount_str = request.form.get("target_amount", "").strip()
        current_amount_str = request.form.get("current_amount", "").strip()
        target_date_str = request.form.get("target_date", "").strip()

        errors = []

        if not goal_name:
            errors.append("Goal name cannot be empty.")
        elif len(goal_name) > 100:
            errors.append("Goal name cannot exceed 100 characters.")

        try:
            target_amount = float(target_amount_str)
            if target_amount <= 0:
                errors.append("Target amount must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid numeric target amount.")

        try:
            current_amount = float(current_amount_str)
            if current_amount < 0:
                errors.append("Current amount cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid numeric current amount.")

        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Please provide a valid target date in YYYY-MM-DD format.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("edit_goal.html", goal=goal)

        goal.goal_name = goal_name
        goal.target_amount = round(target_amount, 2)
        goal.current_amount = round(current_amount, 2)
        goal.target_date = target_date
        goal.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        flash(f"Successfully updated savings goal: {goal_name}!", "success")
        return redirect(url_for("goals.list_goals"))

    return render_template("edit_goal.html", goal=goal)


@goals_bp.route("/<int:goal_id>/delete", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    name = goal.goal_name
    db.session.delete(goal)
    db.session.commit()
    flash(f"Deleted savings goal: {name}.", "info")
    return redirect(url_for("goals.list_goals"))
