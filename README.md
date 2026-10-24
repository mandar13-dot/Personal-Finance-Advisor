# 💰 Personal Finance Advisor & AI Wealth Assistant

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

An intelligent, full-stack personal finance web application built with **Flask**, **SQLAlchemy**, and **Google Gemini AI**. It combines a deterministic transaction ledger with AI-driven insights to help users track cash flows, enforce monthly budgets, achieve savings goals, and receive customized financial recommendations.

---

## 📑 Table of Contents
- [✨ Key Features](#-key-features)
- [🛠️ Tech Stack](#️-tech-stack)
- [🏗️ Architecture & Design](#️-architecture--design)
- [📂 Project Directory Structure](#-project-directory-structure)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [⚙️ Environment Variables](#️-environment-variables)
- [🤖 AI Financial Advisor Engine](#-ai-financial-advisor-engine)
- [🔒 Security & Privacy](#-security--privacy)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Key Features

- **🔐 Secure User Authentication**: Multi-user support with hashed passwords (via Werkzeug), session authentication (Flask-Login), and strict multi-tenant data isolation.
- **📊 Interactive Dashboard**: High-level snapshot of Total Balance, Monthly Earnings, Monthly Spending, Active Savings Goals, and recent ledger activity.
- **💸 Income & Expense Management**: Fast, intuitive logging of earnings and categorized expenditures (Food, Rent, Transport, Entertainment, Shopping, Utilities, Education, Healthcare, Other).
- **🎯 Dynamic Monthly Budgeting**: Set spending ceilings per month (`YYYY-MM`) with real-time remaining calculations and visual alerts when budgets are approached or exceeded.
- **🏆 Milestone-Driven Savings Goals**: Create named savings targets, contribute funds incrementally, and monitor visual completion percentages.
- **📈 Comprehensive Monthly Reports**: Detailed cash flow statements, savings rates, and proportional category-distribution charts.
- **🧠 Two-Tier AI Financial Advisory**:
  - **Tier 1 (Deterministic Math)**: Direct database computation of cash flow, savings rates, burn rates, and top expenditure drivers.
  - **Tier 2 (Gemini LLM Synthesis)**: Analyzes factual metrics to deliver 6 structured, actionable recommendations with zero hallucination.

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | [Python](https://www.python.org/) 3.12+ / [Flask](https://flask.palletsprojects.com/) 3.1 | Application Factory pattern, modular Blueprint architecture |
| **ORM & Database** | [SQLAlchemy](https://www.sqlalchemy.org/) / SQLite | Relational schema with cascade deletions & foreign keys |
| **Authentication** | [Flask-Login](https://flask-login.readthedocs.io/) | Session persistence and `@login_required` access control |
| **Security** | [Werkzeug](https://palletsprojects.com/p/werkzeug/) | Cryptographic password hashing (`scrypt`/`pbkdf2`) |
| **Artificial Intelligence** | [Google Gemini 1.5 Flash](https://ai.google.dev/) | REST API integration via native Python `urllib` |
| **Configuration** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable isolation (`.env`) |
| **Frontend** | HTML5, Jinja2, Vanilla CSS3 | Responsive layouts, CSS variables, progress meters, no bloated JS frameworks |

---

## 🏗️ Architecture & Design

The application follows an **MVC (Model-View-Controller) / Service-Layer** architecture:

```
                  ┌────────────────────────┐
                  │   User (Web Browser)   │
                  └───────────┬────────────┘
                              │ HTTP Requests
                              ▼
                  ┌────────────────────────┐
                  │    Flask Blueprints    │
                  │ (Controllers & Routes) │
                  └──────┬──────────┬──────┘
                         │          │
         ┌───────────────┘          └───────────────┐
         ▼                                          ▼
┌──────────────────┐                       ┌──────────────────┐
│ SQLAlchemy ORM   │                       │  Advisor Service │
│ & SQLite Models  │                       │  (Math + AI)     │
└────────┬─────────┘                       └────────┬─────────┘
         │                                          │
         │ Database Queries                         │ REST Prompts
         ▼                                          ▼
┌──────────────────┐                       ┌──────────────────┐
│  finance.db      │                       │ Google Gemini AI │
└──────────────────┘                       └──────────────────┘
```

---

## 📂 Project Directory Structure

```plaintext
Personal-Finance-Advisor/
├── app/
│   ├── models/             # SQLAlchemy Database Models
│   │   ├── user.py         # User credentials & authentication model
│   │   ├── income.py       # Income records
│   │   ├── expense.py      # Expense categories & logs
│   │   ├── budget.py       # Monthly budget constraints
│   │   └── savings_goal.py # Savings goals & dynamic progress properties
│   ├── routes/             # Blueprint Route Controllers
│   │   ├── auth.py         # Login, Registration, Logout
│   │   ├── main.py         # Dashboard & landing views
│   │   ├── income.py       # Income entry management
│   │   ├── expense.py      # Expense logging
│   │   ├── budget.py       # Budget creation & tracking
│   │   ├── goals.py        # Savings goals & deposits
│   │   ├── reports.py      # Monthly statement & breakdown
│   │   └── advisor.py      # AI Advisor endpoint
│   ├── services/           # Domain Logic
│   │   └── advisor_service.py # Deterministic math + Gemini API integration
│   ├── static/             # Static Assets (CSS, JS, Icons)
│   ├── templates/          # Jinja2 HTML Templates
│   ├── extensions.py       # Initialized db & login_manager instances
│   └── __init__.py         # Flask Application Factory
├── instance/               # SQLite database directory (finance.db)
├── .env.example            # Sample environment variables
├── package.json            # Node/npm run scripts
├── requirements.txt        # Python package dependencies
├── run.py                  # Server entry point
└── README.md               # Project documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- **Python 3.10+** installed
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/mandar13-dot/Personal-Finance-Advisor.git
cd Personal-Finance-Advisor
```

### 3. Setup Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root folder:
```env
SECRET_KEY=your-super-secret-key-change-this
DATABASE_URL=sqlite:///finance.db
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

> **Note**: A free Google Gemini API key can be generated at [Google AI Studio](https://aistudio.google.com/). If omitted, the application runs normally in fallback mode, showing all calculated financial charts.

### 6. Run the Application
```bash
python run.py
```
Or with npm:
```bash
npm start
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🤖 AI Financial Advisor Engine

The advisor feature provides 6 structured modules tailored to your actual numbers:

1. **Financial Summary**: High-level balance sheet and cash flow health.
2. **Spending Insights**: Deep dive into highest expenditure drivers.
3. **Budget Analysis**: Monthly spending velocity and limits adherence.
4. **Savings Analysis**: Progress report across active financial goals.
5. **Personalized Recommendations**: Tactical recommendations to reduce unnecessary spending.
6. **Suggested Next Steps**: Prioritized checklist of 3-4 immediate actions.

---

## 🔒 Security & Privacy

- **Zero-PII Prompts**: User emails, names, passwords, and database IDs are never transmitted to the Gemini API. Only anonymized aggregations are passed.
- **Multi-Tenant Scoping**: All database queries are filtered with `filter_by(user_id=current_user.id)` to prevent IDOR (Insecure Direct Object Reference) vulnerabilities.
- **Secure Hashing**: Passwords are saved as salted hashes via Werkzeug.
- **Graceful Degradation**: If network drops or the AI key is unavailable, the application remains fully functional with ledger analytics.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
