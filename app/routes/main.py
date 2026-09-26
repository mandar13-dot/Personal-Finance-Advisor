from datetime import date
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.income import Income
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.savings_goal import SavingsGoal

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    if today.month == 12:
        start_of_next_month = date(today.year + 1, 1, 1)
    else:
        start_of_next_month = date(today.year, today.month + 1, 1)

    # 1. Calculate logged-in user's income for the current month
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

    current_month_income_count = (
        Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= start_of_month,
            Income.date < start_of_next_month,
        ).count()
    )

    # 2. Calculate logged-in user's expenses for the current month
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

    current_month_expense_count = (
        Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        ).count()
    )

    # 3. Net Savings = Monthly Income - Monthly Expenses
    savings = monthly_income - monthly_expenses
    savings_str = f"₹{savings:,.2f}" if savings >= 0 else f"-₹{abs(savings):,.2f}"

    # 4. Monthly Budget & Budget Remaining calculation
    current_month_key = today.strftime("%Y-%m")
    current_budget = Budget.query.filter_by(
        user_id=current_user.id,
        month=current_month_key,
    ).first()

    if current_budget:
        has_budget = True
        monthly_budget = current_budget.amount
        budget_remaining = monthly_budget - monthly_expenses
        budget_exceeded = monthly_expenses > monthly_budget
        if budget_remaining >= 0:
            budget_remaining_display = f"₹{budget_remaining:,.2f}"
        else:
            budget_remaining_display = f"-₹{abs(budget_remaining):,.2f}"
    else:
        has_budget = False
        monthly_budget = 0.0
        budget_remaining = 0.0
        budget_exceeded = False
        budget_remaining_display = "₹0.00"

    # 5. Fetch recent transactions for logged-in user
    user_incomes = (
        Income.query.filter_by(user_id=current_user.id)
        .order_by(Income.date.desc(), Income.id.desc())
        .limit(10)
        .all()
    )

    user_expenses = (
        Expense.query.filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc(), Expense.id.desc())
        .limit(10)
        .all()
    )

    transactions = []
    for inc in user_incomes:
        transactions.append({
            "type": "income",
            "title": inc.source,
            "category": "Income",
            "amount": inc.amount,
            "date": inc.date,
            "created_at": inc.created_at,
        })

    for exp in user_expenses:
        transactions.append({
            "type": "expense",
            "title": exp.description if exp.description else exp.category,
            "category": exp.category,
            "amount": exp.amount,
            "date": exp.date,
            "created_at": exp.created_at,
        })

    transactions.sort(key=lambda t: (t["date"], t["created_at"]), reverse=True)
    recent_transactions = transactions[:10]

    # 6. Savings Goals summary for logged-in user
    savings_goals = (
        SavingsGoal.query.filter_by(user_id=current_user.id)
        .order_by(SavingsGoal.created_at.desc())
        .limit(4)
        .all()
    )
    total_goals_count = SavingsGoal.query.filter_by(user_id=current_user.id).count()

    current_month_name = today.strftime("%B %Y")

    return render_template(
        "dashboard.html",
        monthly_income=monthly_income,
        monthly_income_display=f"₹{monthly_income:,.2f}",
        total_expenses=monthly_expenses,
        total_expenses_display=f"₹{monthly_expenses:,.2f}",
        savings=savings,
        savings_display=savings_str,
        has_budget=has_budget,
        monthly_budget=monthly_budget,
        budget_remaining=budget_remaining,
        budget_remaining_display=budget_remaining_display,
        budget_exceeded=budget_exceeded,
        abs_budget_remaining=abs(budget_remaining),
        current_month_income_count=current_month_income_count,
        current_month_expense_count=current_month_expense_count,
        current_month_name=current_month_name,
        recent_transactions=recent_transactions,
        savings_goals=savings_goals,
        total_goals_count=total_goals_count,
    )


@main_bp.route("/add-income")
@login_required
def add_income_alias():
    return redirect(url_for("income.add_income"))


@main_bp.route("/add-expense")
@login_required
def add_expense_alias():
    return redirect(url_for("expense.add_expense"))


@main_bp.route("/set-budget")
@login_required
def set_budget_alias():
    return redirect(url_for("budget.manage_budget"))


@main_bp.route("/goals")
@main_bp.route("/savings-goals")
@login_required
def goals_alias():
    return redirect(url_for("goals.list_goals"))