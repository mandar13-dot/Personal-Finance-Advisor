from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.advisor_service import (
    calculate_financial_analysis,
    get_ai_advisor_insights,
)

advisor_bp = Blueprint("advisor", __name__, url_prefix="/advisor")


@advisor_bp.route("/", methods=["GET", "POST"])
@advisor_bp.route("/monthly", methods=["GET", "POST"])
@login_required
def advisor_dashboard():
    """
    Main AI Financial Advisor route.
    Gathers real financial data for current_user, runs backend calculation layer,
    and requests/presents Gemini AI insights.
    """
    # Check if a specific month was submitted via GET query or POST form
    month_param = None
    if request.method == "POST":
        month_param = request.form.get("month", "").strip()
        # Optional refresh action
        if request.form.get("action") == "refresh":
            flash("AI financial analysis refreshed with your latest transactions.", "info")
            return redirect(url_for("advisor.advisor_dashboard", month=month_param or None))
    else:
        month_param = request.args.get("month", "").strip()

    # 1. Deterministic Backend Financial Analysis Layer
    analysis = calculate_financial_analysis(current_user.id, month_str=month_param)

    # 2. AI Recommendation Generation Layer
    ai_insights = get_ai_advisor_insights(analysis)

    return render_template(
        "advisor.html",
        analysis=analysis,
        ai=ai_insights,
        selected_month=analysis["month_key"],
        month_title=analysis["month_title"],
    )


@advisor_bp.route("/refresh", methods=["POST"])
@login_required
def refresh_advice():
    """Explicit refresh endpoint for AI advice."""
    month_param = request.form.get("month", "").strip()
    flash("Financial analysis refreshed successfully.", "success")
    return redirect(url_for("advisor.advisor_dashboard", month=month_param or None))
