from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.income import Income
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.savings_goal import SavingsGoal

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/", methods=["GET", "POST"])
@reports_bp.route("/monthly", methods=["GET", "POST"])
@login_required
def monthly_report():
    today = date.today()
    default_month_str = today.strftime("%Y-%m")

    # If POST, redirect to clean GET with month query parameter
    if request.method == "POST":
        month_param = request.form.get("month", "").strip()
        return redirect(url_for("reports.monthly_report", month=month_param or default_month_str))

    month_str = request.args.get("month", "").strip()
    if not month_str:
        month_str = default_month_str

    try:
        selected_date = datetime.strptime(month_str, "%Y-%m").date()
    except (ValueError, TypeError):
        month_str = default_month_str
        selected_date = today

    start_of_month = date(selected_date.year, selected_date.month, 1)
    if selected_date.month == 12:
        start_of_next_month = date(selected_date.year + 1, 1, 1)
    else:
        start_of_next_month = date(selected_date.year, selected_date.month + 1, 1)

    month_title = selected_date.strftime("%B %Y")
    month_key = selected_date.strftime("%Y-%m")

    # 1. Total Monthly Income
    monthly_income = (
        db.session.query(func.coalesce(func.sum(Income.amount), 0.0))
        .filter(
            Income.user_id == current_user.id,
            Income.date >= start_of_month,
            Income.date < start_of_next_month,
        )
        .scalar()
        or 0.0
    )

    income_transactions = (
        Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= start_of_month,
            Income.date < start_of_next_month,
        )
        .order_by(Income.date.desc(), Income.id.desc())
        .all()
    )
    income_count = len(income_transactions)

    # 2. Total Monthly Expenses
    monthly_expenses = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        )
        .scalar()
        or 0.0
    )

    expense_transactions = (
        Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        )
        .order_by(Expense.date.desc(), Expense.id.desc())
        .all()
    )
    expense_count = len(expense_transactions)

    # 3. Net Savings
    net_savings = monthly_income - monthly_expenses
    savings_rate = round((net_savings / monthly_income) * 100, 1) if monthly_income > 0 else 0.0

    # 4. Category-wise Expense Breakdown
    category_records = (
        db.session.query(
            Expense.category,
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("tx_count"),
        )
        .filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    category_breakdown = []
    for cat, total, count in category_records:
        pct = round((total / monthly_expenses) * 100, 1) if monthly_expenses > 0 else 0.0
        category_breakdown.append({
            "category": cat,
            "total": total,
            "count": count,
            "percentage": pct,
        })

    # 5. Monthly Budget Information
    budget_record = Budget.query.filter_by(
        user_id=current_user.id,
        month=month_key,
    ).first()

    if budget_record:
        has_budget = True
        budget_amount = budget_record.amount
        budget_remaining = budget_amount - monthly_expenses
        budget_exceeded = monthly_expenses > budget_amount
        budget_usage_pct = round((monthly_expenses / budget_amount) * 100, 1) if budget_amount > 0 else 0.0
    else:
        has_budget = False
        budget_amount = 0.0
        budget_remaining = 0.0
        budget_exceeded = False
        budget_usage_pct = 0.0

    # 6. Savings Goals Summary
    savings_goals = (
        SavingsGoal.query.filter_by(user_id=current_user.id)
        .order_by(SavingsGoal.created_at.desc())
        .all()
    )
    total_goals_target = sum(g.target_amount for g in savings_goals)
    total_goals_saved = sum(g.current_amount for g in savings_goals)
    total_goals_remaining = sum(g.remaining_amount for g in savings_goals)
    overall_goals_pct = round((total_goals_saved / total_goals_target) * 100, 1) if total_goals_target > 0 else 0.0

    # 7. Complete Transactions for the Month
    month_transactions = []
    for inc in income_transactions:
        month_transactions.append({
            "type": "income",
            "title": inc.source,
            "category": "Income",
            "amount": inc.amount,
            "date": inc.date,
            "created_at": inc.created_at,
        })
    for exp in expense_transactions:
        month_transactions.append({
            "type": "expense",
            "title": exp.description if exp.description else exp.category,
            "category": exp.category,
            "amount": exp.amount,
            "date": exp.date,
            "created_at": exp.created_at,
        })
    month_transactions.sort(key=lambda t: (t["date"], t["created_at"]), reverse=True)

    has_data = (income_count > 0 or expense_count > 0 or has_budget)

    return render_template(
        "report.html",
        month_key=month_key,
        month_title=month_title,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,
        income_count=income_count,
        expense_count=expense_count,
        category_breakdown=category_breakdown,
        has_budget=has_budget,
        budget_amount=budget_amount,
        budget_remaining=budget_remaining,
        budget_exceeded=budget_exceeded,
        abs_budget_remaining=abs(budget_remaining),
        budget_usage_pct=budget_usage_pct,
        savings_goals=savings_goals,
        total_goals_target=total_goals_target,
        total_goals_saved=total_goals_saved,
        total_goals_remaining=total_goals_remaining,
        overall_goals_pct=overall_goals_pct,
        month_transactions=month_transactions,
        has_data=has_data,
    )
