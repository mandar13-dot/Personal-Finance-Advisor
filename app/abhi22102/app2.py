from flask import Flask

app2 = Flask(__name__)


@app2.route("/")
def home():
    return "Personal Finance Advisor Bot is running!"


if __name__ == "__main__":
    app2.run(debug=True)

@app2.route("/about")
def about():
    return "This is the Personal Finance Advisor Bot."    