from flask import Flask, render_template

app = Flask(__name__)

# หน้า 1 - หน้าโครงงาน
@app.route("/")
def home():
    return render_template("index.html")

# หน้า 2 - คณะผู้จัดทำ
@app.route("/team")
def team():
    return render_template("team.html")

# หน้า 5 - เมนูสั่งน้ำ
@app.route("/menu")
def menu():
    return render_template("menu.html")

if __name__ == "__main__":
    app.run(debug=True)
