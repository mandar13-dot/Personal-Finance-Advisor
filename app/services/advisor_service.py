import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, date
from sqlalchemy import func

from app.extensions import db
from app.models.income import Income
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.savings_goal import SavingsGoal


def calculate_financial_analysis(user_id, month_str=None):
    """
    Computes deterministic financial facts and metrics strictly for the given user_id.
    Never uses fake data. Scoped strictly to user_id.
    """
    today = date.today()
    default_month_key = today.strftime("%Y-%m")

    # Determine which month to analyze
    target_month_key = (month_str or "").strip()
    selected_date = None

    if target_month_key:
        try:
            selected_date = datetime.strptime(target_month_key, "%Y-%m").date()
        except (ValueError, TypeError):
            selected_date = None

    if not selected_date:
        # Check if current month has any data
        cur_start = date(today.year, today.month, 1)
        cur_next = date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)
        cur_has_inc = Income.query.filter(Income.user_id == user_id, Income.date >= cur_start, Income.date < cur_next).first()
        cur_has_exp = Expense.query.filter(Expense.user_id == user_id, Expense.date >= cur_start, Expense.date < cur_next).first()
        cur_has_bgt = Budget.query.filter_by(user_id=user_id, month=default_month_key).first()

        if cur_has_inc or cur_has_exp or cur_has_bgt:
            selected_date = today
        else:
            # Check latest transaction date if any
            latest_inc = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc()).first()
            latest_exp = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).first()
            dates = [d for d in [latest_inc.date if latest_inc else None, latest_exp.date if latest_exp else None] if d]
            if dates:
                selected_date = max(dates)
            else:
                latest_bgt = Budget.query.filter_by(user_id=user_id).order_by(Budget.month.desc()).first()
                if latest_bgt:
                    try:
                        selected_date = datetime.strptime(latest_bgt.month, "%Y-%m").date()
                    except (ValueError, TypeError):
                        selected_date = today
                else:
                    selected_date = today

    month_key = selected_date.strftime("%Y-%m")
    month_title = selected_date.strftime("%B %Y")
    start_of_month = date(selected_date.year, selected_date.month, 1)
    if selected_date.month == 12:
        start_of_next_month = date(selected_date.year + 1, 1, 1)
    else:
        start_of_next_month = date(selected_date.year, selected_date.month + 1, 1)

    # 1. Incomes for the period
    monthly_income = (
        db.session.query(func.coalesce(func.sum(Income.amount), 0.0))
        .filter(
            Income.user_id == user_id,
            Income.date >= start_of_month,
            Income.date < start_of_next_month,
        )
        .scalar()
        or 0.0
    )

    income_transactions = (
        Income.query.filter(
            Income.user_id == user_id,
            Income.date >= start_of_month,
            Income.date < start_of_next_month,
        )
        .order_by(Income.date.desc(), Income.id.desc())
        .all()
    )
    income_count = len(income_transactions)

    # 2. Expenses for the period
    monthly_expenses = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(
            Expense.user_id == user_id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        )
        .scalar()
        or 0.0
    )

    expense_transactions = (
        Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date >= start_of_month,
            Expense.date < start_of_next_month,
        )
        .order_by(Expense.date.desc(), Expense.id.desc())
        .all()
    )
    expense_count = len(expense_transactions)

    # 3. Net Savings & Savings Rate
    net_savings = monthly_income - monthly_expenses
    savings_rate = round((net_savings / monthly_income) * 100, 1) if monthly_income > 0 else 0.0

    # 4. Category Breakdown & Highest Category
    category_records = (
        db.session.query(
            Expense.category,
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("tx_count"),
        )
        .filter(
            Expense.user_id == user_id,
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

    highest_category = None
    if category_breakdown:
        highest_category = {
            "category": category_breakdown[0]["category"],
            "total": category_breakdown[0]["total"],
            "percentage": category_breakdown[0]["percentage"],
        }

    # 5. Budget Information
    budget_record = Budget.query.filter_by(
        user_id=user_id,
        month=month_key,
    ).first()

    if budget_record:
        has_budget = True
        budget_amount = budget_record.amount
        budget_remaining = budget_amount - monthly_expenses
        budget_exceeded = monthly_expenses > budget_amount
        budget_exceeded_amount = max(0.0, monthly_expenses - budget_amount)
        budget_usage_pct = round((monthly_expenses / budget_amount) * 100, 1) if budget_amount > 0 else 0.0
    else:
        has_budget = False
        budget_amount = 0.0
        budget_remaining = 0.0
        budget_exceeded = False
        budget_exceeded_amount = 0.0
        budget_usage_pct = 0.0

    # 6. Savings Goals
    savings_goals = (
        SavingsGoal.query.filter_by(user_id=user_id)
        .order_by(SavingsGoal.created_at.desc())
        .all()
    )
    goals_count = len(savings_goals)
    total_goals_target = sum(g.target_amount for g in savings_goals)
    total_goals_saved = sum(g.current_amount for g in savings_goals)
    total_goals_remaining = sum(g.remaining_amount for g in savings_goals)
    overall_goals_pct = round((total_goals_saved / total_goals_target) * 100, 1) if total_goals_target > 0 else 0.0

    goals_list = []
    for g in savings_goals:
        goals_list.append({
            "id": g.id,
            "name": g.goal_name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "remaining_amount": g.remaining_amount,
            "progress_percentage": g.progress_percentage,
            "is_completed": g.is_completed,
            "target_date": g.target_date.strftime("%b %d, %Y") if g.target_date else None,
        })

    # 7. Recent Transactions (latest 10 across all time for this user)
    all_recent_inc = Income.query.filter_by(user_id=user_id).order_by(Income.date.desc(), Income.id.desc()).limit(10).all()
    all_recent_exp = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc(), Expense.id.desc()).limit(10).all()
    recent_transactions = []
    for inc in all_recent_inc:
        recent_transactions.append({
            "type": "income",
            "title": inc.source,
            "category": "Income",
            "amount": inc.amount,
            "date": inc.date,
            "created_at": inc.created_at,
        })
    for exp in all_recent_exp:
        recent_transactions.append({
            "type": "expense",
            "title": exp.description if exp.description else exp.category,
            "category": exp.category,
            "amount": exp.amount,
            "date": exp.date,
            "created_at": exp.created_at,
        })
    recent_transactions.sort(key=lambda t: (t["date"], t["created_at"]), reverse=True)
    recent_transactions = recent_transactions[:8]

    # 8. Deterministic Spending Patterns & Financial Observations
    spending_patterns = []
    if monthly_income > 0 and monthly_expenses > 0:
        if net_savings >= 0:
            spending_patterns.append(
                f"Positive monthly cash flow of ₹{net_savings:,.2f} with a {savings_rate}% savings rate."
            )
        else:
            spending_patterns.append(
                f"Monthly deficit of ₹{abs(net_savings):,.2f}: spending exceeds income by {round((abs(net_savings) / monthly_income) * 100, 1)}%."
            )
    elif monthly_income > 0 and monthly_expenses == 0:
        spending_patterns.append(f"Recorded income of ₹{monthly_income:,.2f} with zero expenses logged this period.")
    elif monthly_income == 0 and monthly_expenses > 0:
        spending_patterns.append(f"Expenses totaling ₹{monthly_expenses:,.2f} recorded without any logged income for {month_title}.")

    if highest_category:
        spending_patterns.append(
            f"{highest_category['category']} is your highest expense at ₹{highest_category['total']:,.2f}, accounting for {highest_category['percentage']}% of total expenditures."
        )

    if has_budget:
        if budget_exceeded:
            spending_patterns.append(
                f"Budget exceeded by ₹{budget_exceeded_amount:,.2f} ({budget_usage_pct}% of the ₹{budget_amount:,.2f} monthly limit)."
            )
        else:
            spending_patterns.append(
                f"Within budget limit: ₹{budget_remaining:,.2f} remaining out of ₹{budget_amount:,.2f} ({budget_usage_pct}% spent)."
            )
    else:
        spending_patterns.append(f"No monthly budget set for {month_title}.")

    if goals_count > 0:
        spending_patterns.append(
            f"Active savings goals: {goals_count} goal(s) totaling ₹{total_goals_target:,.2f}, currently {overall_goals_pct}% funded (₹{total_goals_saved:,.2f} saved)."
        )
    else:
        spending_patterns.append("No active savings goals defined yet.")

    # 9. Overall data availability check
    has_data = bool(
        monthly_income > 0
        or monthly_expenses > 0
        or has_budget
        or goals_count > 0
        or len(recent_transactions) > 0
    )

    return {
        "user_id": user_id,
        "month_key": month_key,
        "month_title": month_title,
        "has_data": has_data,
        "monthly_income": monthly_income,
        "income_count": income_count,
        "monthly_expenses": monthly_expenses,
        "expense_count": expense_count,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "category_breakdown": category_breakdown,
        "highest_category": highest_category,
        "budget_info": {
            "has_budget": has_budget,
            "amount": budget_amount,
            "remaining": budget_remaining,
            "exceeded": budget_exceeded,
            "exceeded_amount": budget_exceeded_amount,
            "usage_pct": budget_usage_pct,
        },
        "goals_info": {
            "count": goals_count,
            "total_target": total_goals_target,
            "total_saved": total_goals_saved,
            "total_remaining": total_goals_remaining,
            "overall_pct": overall_goals_pct,
            "goals": goals_list,
        },
        "recent_transactions": recent_transactions,
        "spending_patterns": spending_patterns,
    }


def call_gemini_api(api_key, prompt, model=None, timeout=15):
    """
    Sends prompt to the Gemini API using standard library urllib.request.
    Can be easily mocked in automated tests.
    """
    model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        resp_data = json.loads(response.read().decode("utf-8"))

    candidates = resp_data.get("candidates", [])
    if not candidates:
        raise ValueError("No response candidates returned by Gemini API.")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts or "text" not in parts[0]:
        raise ValueError("Invalid content structure in Gemini API response.")

    return parts[0]["text"]


def parse_ai_sections(raw_text):
    """
    Parses the 6 structured sections from AI markdown response text.
    Handles various markdown formatting styles gracefully.
    """
    if not raw_text:
        return None

    sections = {
        "financial_summary": "",
        "spending_insights": "",
        "budget_analysis": "",
        "savings_analysis": "",
        "recommendations": "",
        "next_steps": "",
    }

    # Normalize line endings
    text = raw_text.replace("\r\n", "\n")

    patterns = [
        ("financial_summary", r"###?\s*(?:1[\.\)]?\s*)?Financial Summary\s*\n(.*?)(?=###?|\Z)"),
        ("spending_insights", r"###?\s*(?:2[\.\)]?\s*)?Spending Insights\s*\n(.*?)(?=###?|\Z)"),
        ("budget_analysis", r"###?\s*(?:3[\.\)]?\s*)?Budget Analysis\s*\n(.*?)(?=###?|\Z)"),
        ("savings_analysis", r"###?\s*(?:4[\.\)]?\s*)?Savings Analysis\s*\n(.*?)(?=###?|\Z)"),
        ("recommendations", r"###?\s*(?:5[\.\)]?\s*)?Personalized Recommendations\s*\n(.*?)(?=###?|\Z)"),
        ("next_steps", r"###?\s*(?:6[\.\)]?\s*)?Suggested Next Steps\s*\n(.*?)(?=###?|\Z)"),
    ]

    has_parsed_any = False
    for key, pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
            has_parsed_any = True

    if not has_parsed_any:
        # Fallback: keep text in financial_summary so it is displayed in UI
        sections["financial_summary"] = text.strip()

    return sections


def get_ai_advisor_insights(analysis_data, api_key=None, model=None):
    """
    Coordinates AI recommendation generation:
    1. Validates real financial data exists.
    2. Validates GEMINI_API_KEY.
    3. Builds privacy-safe structured prompt with zero credentials.
    4. Invokes Gemini API safely.
    5. Returns structured response with graceful error handling.
    """
    # 1. Handle users with empty data
    if not analysis_data.get("has_data"):
        return {
            "status": "empty_data",
            "available": False,
            "message": "No financial data available yet. Please record your income, log expenses, set a budget, or create savings goals to receive AI-powered financial advice.",
            "sections": None,
            "raw_text": None,
        }

    # 2. Check API key
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or not key.strip():
        return {
            "status": "missing_key",
            "available": False,
            "message": "AI recommendations are currently unavailable because the Gemini API key is not configured. Set GEMINI_API_KEY in your environment to activate AI insights. Your calculated financial analysis is displayed below.",
            "sections": None,
            "raw_text": None,
        }

    # 3. Construct structured prompt (NO personal credentials, passwords, or emails)
    cat_details = ", ".join([f"{c['category']}: ₹{c['total']:,.2f} ({c['percentage']}%)" for c in analysis_data["category_breakdown"]]) or "None logged"
    highest_str = f"{analysis_data['highest_category']['category']} (₹{analysis_data['highest_category']['total']:,.2f}, {analysis_data['highest_category']['percentage']}%)" if analysis_data.get("highest_category") else "None"
    
    b_info = analysis_data["budget_info"]
    if b_info["has_budget"]:
        b_str = f"Monthly Limit: ₹{b_info['amount']:,.2f}, Spent: ₹{analysis_data['monthly_expenses']:,.2f}, " + (
            f"Exceeded by: ₹{b_info['exceeded_amount']:,.2f} ({b_info['usage_pct']}% utilized)"
            if b_info["exceeded"]
            else f"Remaining: ₹{b_info['remaining']:,.2f} ({b_info['usage_pct']}% utilized)"
        )
    else:
        b_str = "No budget established for this month"

    g_info = analysis_data["goals_info"]
    if g_info["count"] > 0:
        goals_strs = [f"{g['name']}: ₹{g['current_amount']:,.2f} saved of ₹{g['target_amount']:,.2f} ({g['progress_percentage']}%)" for g in g_info["goals"]]
        g_str = f"{g_info['count']} goal(s), overall {g_info['overall_pct']}% funded. Details: " + "; ".join(goals_strs)
    else:
        g_str = "No savings goals created"

    patterns_str = "\n".join([f"- {p}" for p in analysis_data["spending_patterns"]])

    prompt = f"""You are a professional Personal Financial Advisor assisting an authenticated user.
Analyze the following REAL financial facts for the month of {analysis_data['month_title']}.
All monetary amounts are strictly in Indian Rupees (₹).

REAL FINANCIAL FACTS (Calculated from User Ledger):
- Period: {analysis_data['month_title']}
- Total Monthly Income: ₹{analysis_data['monthly_income']:,.2f} ({analysis_data['income_count']} transaction(s))
- Total Monthly Expenses: ₹{analysis_data['monthly_expenses']:,.2f} ({analysis_data['expense_count']} transaction(s))
- Net Savings: ₹{analysis_data['net_savings']:,.2f}
- Savings Rate: {analysis_data['savings_rate']}% of income
- Highest Spending Category: {highest_str}
- Category Breakdown: {cat_details}
- Budget Status: {b_str}
- Savings Goals: {g_str}
- Key Observational Patterns:
{patterns_str}

STRICT INSTRUCTIONS:
1. Base all observations and recommendations strictly on the provided real data above. Do NOT invent fake transactions, imaginary figures, or unrecorded goals.
2. Clearly distinguish calculated financial facts from actionable advice.
3. Address the highest spending category and specific budget/savings numbers directly.
4. Always use Indian Rupees (₹).
5. Format your response into exactly these 6 sections using the exact markdown headings below:

### Financial Summary
(A concise, executive summary of cash flow, income versus expenses, and overall financial health)

### Spending Insights
(Deep dive into the category spending breakdown, specifically analyzing the highest spending category)

### Budget Analysis
(Evaluation of the monthly budget adherence, remaining funds or over-budget amounts, and spending velocity)

### Savings Analysis
(Assessment of the user's savings rate and progress toward their active savings goals)

### Personalized Recommendations
(Specific, actionable suggestions tailored to their actual figures to reduce expenses and optimize savings)

### Suggested Next Steps
(A prioritized list of 3-4 concrete actions the user can take right now)
"""

    # 4. Invoke API safely
    try:
        raw_text = call_gemini_api(key.strip(), prompt, model=model)
        sections = parse_ai_sections(raw_text)
        return {
            "status": "success",
            "available": True,
            "message": "AI financial analysis generated successfully based on your real records.",
            "sections": sections,
            "raw_text": raw_text,
        }
    except Exception as e:
        return {
            "status": "api_error",
            "available": False,
            "message": f"AI recommendations service error ({type(e).__name__}: {str(e)}). Your calculated financial analysis is displayed below.",
            "sections": None,
            "raw_text": None,
        }
