from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_session import Session
import pymongo
from datetime import datetime
import pytz

client = pymongo.MongoClient(
    "your mongodb link here")
db = client["database"]

today_ = ""
time_ = "0"
check = 0


def reload():
    global today_
    global time_
    global check

    timezone = pytz.timezone('Asia/Kolkata')
    today_ = datetime.now(timezone).strftime("%A")[:3].lower()
    time_ = datetime.now(timezone).hour

    if today_ == "sat" and check == 0:
        coll = db["faculty_schedule"]
        coll.delete_many({})
        coll = db["student_schedule"]
        coll.delete_many({})
        coll = db["slots_list"]
        coll.delete_many({})
        check = 1

    if today_ == "mon":
        check = 0

    for x in ["mon", "tue", "wed", "thu", "fri"]:
        if x == today_:
            break
        coll = db["slots_list"]
        f = list(coll.find({"day": x}))
        if len(f):
            coll.update_many({"day": x}, {"$set": {"status": "inactive"}})

    coll = db["slots_list"]
    f = list(coll.find({"day": today_}))
    if len(f):
        for x in f:
            time = int(x["time"])
            if time in [1, 2, 3, 4, 5]:
                time = time+12
            if time <= int(time_):
                coll.update_many({"day": today_, "time": x["time"]}, {
                                 "$set": {"status": "inactive"}})
    return


app = Flask(__name__)
app.secret_key = "WALKER"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/', methods=["POST", "GET"])
def login():
    reload()
    session["id"] = ""
    if request.method == "POST":
        if 'fac_login' in request.form:
            fac_id = request.form.get("fac_id")
            fac_pass = request.form.get("fac_pass")
            session["id"] = fac_id
            coll = db["faculty_cred"]
            f = list(coll.find({"user_name": fac_id}))
            if len(f) != 0:
                coll = db["admin_cred"]
                f = list(coll.find({"user_name": fac_id}))
                if len(f):
                    pass_ = f[0]["password"]
                    if fac_pass == pass_:
                        return redirect(url_for("admin", user_name=fac_id))
                coll = db["faculty_cred"]
                f = coll.find({"user_name": fac_id})[0]
                if f["password"] != fac_pass:
                    print("Password wrong")
                    return redirect(url_for("login"))
                else:
                    return redirect(url_for('faculty', user_name=fac_id))
            else:
                print("User not found")
                return redirect(url_for("login"))
        elif 'stud_login' in request.form:
            stud_roll = request.form.get("stud_roll")
            stud_pass = request.form.get("stud_pass")
            session["id"] = stud_roll
            coll = db["student"]
            f = list(coll.find({"roll": stud_roll}))
            if len(f):
                coll = db["student_cred"]
                x = coll.find({"roll": stud_roll})[0]
                if x["password"] != stud_pass:
                    flash("Password wrong")
                    return redirect(url_for("login"))
                else:
                    return redirect(url_for("student", roll=stud_roll))
            else:
                flash("User not found")
                return redirect(url_for("login"))
    return render_template("login.html")


@app.route('/admin', methods=["POST", "GET"])
def admin():
    reload()
    if session["id"] == "":
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name")
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        email = "user@gamil.com"
        subjects = "X,Y,Z"
        dept = "ABC"
        coll = db["faculty_cred"]
        f = list(coll.find({"user_name": user_name}))
        if not len(f):
            rec = {"user_name": user_name, "password": password}
            coll.insert_one(rec)
            coll = db["faculty"]
            rec = {"name": name, "user_name": user_name,
                   "email": email, "subjects": subjects, "dept": dept}
            coll.insert_one(rec)
            coll = db["faculty_schedule"]
            rec = {"user_name": user_name, "mon": [],
                   "tue": [], "wed": [], "thu": [], "fri": []}
            coll.insert_one(rec)
        else:
            flash("User exists")
    return render_template("admin.html")


@app.route('/signup', methods=["POST", "GET"])
def signup():
    reload()
    if request.method == "POST":
        roll = request.form.get("roll")
        name = request.form.get("name")
        branch = request.form.get("branch")
        sem = request.form.get("sem")
        email = request.form.get("email")
        batch = request.form.get("batch")
        country = request.form.get("country")
        phone = request.form.get("phone")
        password = request.form.get("password")
        conf_password = request.form.get("conf_password")
        if password != conf_password:
            flash("Passwords not matching")
        else:
            coll = db["student_cred"]
            f = list(coll.find({"roll": roll}))
            if not len(f):
                rec = {"roll": roll, "password": password}
                coll.insert_one(rec)
                rec = {"roll": roll, "name": name, "branch": branch, "sem": sem,
                       "email": email, "batch": batch, "country": country, "phone": phone}
                coll = db["student"]
                coll.insert_one(rec)
            else:
                flash("User exists")
    return render_template("signup.html")


@app.route('/student', methods=["POST", "GET"])
def student():
    reload()
    roll = request.args.get('roll')
    if session["id"] == "" or session["id"] != roll:
        return redirect(url_for("login"))
    coll = db["student_schedule"]
    f = list(coll.find({"roll": roll}))
    sched = []
    for x in f:
        if today_ in x:
            time = x[today_]
            user_name = x["user_name"]
            coll = db["faculty"]
            name = list(coll.find({"user_name": user_name}))[0]["name"]
            coll = db["slots_list"]
            if(len(list(coll.find({"user_name": user_name, "time": time, "status": "active"})))):
                sched.append(time+" with "+name+".")
    coll = db["student"]
    name = coll.find({"roll": roll})[0]["name"]
    data = {"name": name, "roll": roll, "sched": sched}
    return render_template("student.html", data=data)


@app.route('/change_password_stu', methods=["POST", "GET"])
def change_password_stu():
    reload()
    roll = request.args.get("roll")
    if session["id"] == "" or session["id"] != roll:
        return redirect(url_for("login"))
    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        conf_pass = request.form.get("confirm_password")
        coll = db["student_cred"]
        f = list(coll.find({"roll": roll}))[0]
        if f["password"] != old_pass:
            flash("wrong password")
        else:
            if new_pass != conf_pass:
                flash("passwords not matched")
            else:
                coll.update_one({"roll": roll}, {
                                "$set": {"password": new_pass}})
                return redirect(url_for("login"))
    data = {"roll": roll}
    return render_template("change_password_stu.html", data=data)


@app.route('/change_password_fac', methods=["POST", "GET"])
def change_password_fac():
    reload()
    user_name = request.args.get("user_name")
    if session["id"] == "" or session["id"] != user_name:
        return redirect(url_for("login"))
    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        conf_pass = request.form.get("confirm_password")
        coll = db["faculty_cred"]
        f = list(coll.find({"user_name": user_name}))[0]
        if f["password"] != old_pass:
            flash("wrong password")
        else:
            if new_pass != conf_pass:
                flash("passwords not matched")
            else:
                coll.update_one({"user_name": user_name}, {
                                "$set": {"password": new_pass}})
                return redirect(url_for("login"))
    data = {"user_name": user_name}
    return render_template("change_password_fac.html", data=data)


@app.route('/appointments', methods=["POST", "GET"])
def appointments():
    reload()
    roll = request.args.get('roll')
    if session["id"] == "" or session["id"] != roll:
        return redirect(url_for("login"))
    coll = db["student"]
    stud_branch = coll.find({"roll": roll})[0]["branch"]
    coll = db["faculty"]
    fac = list(coll.find())
    data = {"roll": roll, "stud_branch": stud_branch, "fac": fac}
    return render_template("appointments.html", data=data)


@app.route('/teacher', methods=["POST", "GET"])
def teacher():
    reload()
    user_name = request.args.get('user_name')
    roll = request.args.get('roll')
    if session["id"] == "" or session["id"] != roll:
        return redirect(url_for("login"))
    if request.method == "POST":
        day = request.form.get("day")
        slot = request.form.get("slot")
        if slot and day != "-":
            coll = db["student_schedule"]
            coll.update_one({"roll": roll, "user_name": user_name}, {
                            "$set": {day: slot}}, True)
            coll = db["slots_list"]
            students = list(
                coll.find({"user_name": user_name, "day": day, "time": slot}))
            if not len(students):
                students = [roll]
            else:
                students = students[0]["students"]
                if roll not in students:
                    students.append(roll)
            coll.update_one({"user_name": user_name, "day": day, "time": slot, "status": "active"}, {
                            "$set": {"students": students}}, True)
    coll = db["faculty"]
    fac = coll.find({"user_name": user_name})[0]
    coll = db["faculty_schedule"]
    t_sched = list(coll.find({"user_name": user_name}))
    if not len(t_sched):
        t_sched = []
    else:
        t_sched = t_sched[0]
    coll = db["student_schedule"]
    s_schedule = list(coll.find({"roll": roll, "user_name": user_name}))
    if not len(s_schedule):
        s_schedule = []
    else:
        s_schedule = s_schedule[0].keys()
    if today_ in ["sat", "sun"]:
        s_schedule = ["mon", "tue", "wed", "thu", "fri"]
    data = {"roll": roll, "teacher": fac,
            "t_sched": t_sched, "s_schedule": s_schedule}
    return render_template("teacher.html", data=data)


@app.route('/status', methods=["POST", "GET"])
def status():
    reload()
    if request.method == "POST":
        num = ""
        for post in request.form:
            if "cancel" in post:
                num = post[6:]
                break
        roll = request.form.get("roll"+num)
        user_name = request.form.get("user_name"+num)
        time = request.form.get("time"+num)
        day = request.form.get("day"+num)
        coll = db["slots_list"]
        f = coll.find({"user_name": user_name, "day": day, "time": time})[0]
        students = f["students"]
        students.remove(roll)
        coll.update_one({"user_name": user_name, "day": day, "time": time}, {
                        "$set": {"students": students}})
        coll = db["student_schedule"]
        coll.update_one({"roll": roll, "user_name": user_name}, {
                        "$unset": {day: ""}})
        return redirect(url_for("status", roll=roll))
    roll = request.args.get('roll')
    if session["id"] == "" or session["id"] != roll:
        return redirect(url_for("login"))
    coll = db["student_schedule"]
    f = list(coll.find({"roll": roll}))
    fac = []
    if len(f):
        for x in f:
            slot = {}
            user_name = x["user_name"]
            slot["user_name"] = user_name
            coll = db["faculty"]
            name = coll.find({"user_name": x["user_name"]})[0]["name"]
            slot["name"] = name
            for key, value in x.items():
                if key not in ["user_name", "roll", "_id"]:
                    coll = db["slots_list"]
                    k = list(
                        coll.find({"user_name": user_name, "day": key, "time": value}))
                    if len(k):
                        status = k[0]["status"]
                        students = k[0]["students"]
                        i = students.index(roll)
                        if i > 1 and status not in ["canceled", "inactive"]:
                            status = "waiting"+"("+"WL "+str(i-1)+")"
                    else:
                        status = "active"
                    slot[key] = {"time": value, "status": status}
            fac.append(slot)
    data = {"roll": roll, "fac": fac}
    return render_template("status.html", data=data)


@app.route('/faculty', methods=["POST", "GET"])
def faculty():
    reload()
    user_name = request.args.get('user_name')
    if session["id"] == "" or session["id"] != user_name:
        return redirect(url_for("login"))
    coll = db["slots_list"]
    f = list(coll.find({"user_name": user_name, "day": today_}))
    sched = []
    for x in f:
        time = x["time"]
        stud = x["students"]
        stud_list = ""
        count = 0
        for s in stud:
            if count == 2:
                break
            coll = db["student"]
            f = list(coll.find({"roll": s}))[0]
            stud_list += f["name"]+" ("+s+") "+","
            count = count+1
        if len(stud):
            coll = db["slots_list"]
            if(len(list(coll.find({"user_name": user_name, "time": time, "status": "active"})))):
                sched.append(time+" with "+stud_list)
    coll = db["faculty"]
    name = coll.find({"user_name": user_name})[0]["name"]
    data = {"user_name": user_name, "name": name, "sched": sched}
    return render_template("faculty.html", data=data)


@app.route('/select_slot', methods=["POST", "GET"])
def select_slot():
    reload()
    user_name = request.args.get('user_name')
    if session["id"] == "" or session["id"] != user_name:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.method == "POST":
            coll = db["faculty_schedule"]
            day = request.form.get("day")
            slot = ["8", "9", "10", "11", "12", "1", "2", "3", "4", "5"]
            times = list(coll.find({"user_name": user_name, "day": day}))
            if len(times):
                times = times[0][day]
            else:
                times = []
            for time in slot:
                if time in request.form:
                    times.append(time)
            coll.update_one({"user_name": user_name}, {
                            "$set": {day: times}}, True)
    coll = db["faculty"]
    x = coll.find({"user_name": user_name})[0]
    coll = db["faculty_schedule"]
    y = list(coll.find({"user_name": user_name}))
    if not len(y):
        y = {}
    else:
        y = y[0]
    days = {"-": "-", "mon": "Monday", "tue": "Tuesday",
            "wed": "Wednesday", "thu": "Thursday", "fri": "Friday"}
    avail_days = {"-": "-", "mon": "Monday", "tue": "Tuesday",
                  "wed": "Wednesday", "thu": "Thursday", "fri": "Friday"}
    if today_ not in ["sat", "sun"]:
        for a, b in days.items():
            if a == today_:
                break
            if a == "-":
                continue
            avail_days.pop(a)
    data = {"user_name": user_name, "name": x["name"], "email": x["email"],
            "dept": x["dept"], "day": y, "avail_days": avail_days, "time_": time_, "today_": today_}
    return render_template("select_slot.html", data=data)


@app.route('/cancel_slot', methods=["POST", "GET"])
def cancel_slot():
    reload()
    user_name = request.args.get('user_name')
    if session["id"] == "" or session["id"] != user_name:
        return redirect(url_for("login"))
    if request.method == "POST":
        day = request.form.get("day")
        slots = []
        for slot in ["8", "9", "10", "11", "12", "1", "2", "3", "4", "5"]:
            if slot in request.form:
                slots.append(slot)
        coll = db["faculty_schedule"]
        f = list(coll.find({"user_name": user_name}))[0]
        times = f[day]
        for slot in slots:
            times.remove(slot)
        coll.update_one({"user_name": user_name}, {"$set": {day: times}})
        coll = db["slots_list"]
        f = list(coll.find({"user_name": user_name, "day": day}))
        for x in f:
            time = x["time"]
            if time in slots:
                coll.update_one({"user_name": user_name, "day": day, "time": time}, {
                                "$set": {"status": "canceled"}})
        coll = db["student_schedule"]
        f = list(coll.find({"user_name": user_name, "day": day}))
        for x in f:
            if x[day] in slots:
                coll.update_one({"user_name": user_name, "day": day}, {
                                "$unset": {day: ""}})
    coll = db["faculty_schedule"]
    data = list(coll.find({"user_name": user_name}))
    if not len(data):
        data = {"user_name": user_name}
    else:
        data = data[0]
    return render_template("cancel_slot.html", data=data)


@app.route('/edit_profile', methods=["POST", "GET"])
def edit_profile():
    reload()
    user_name = request.args.get("user_name")
    if session["id"] == "" or session["id"] != user_name:
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subjects = request.form.get("subjects")
        dept = request.form.get("dept")
        coll = db["faculty"]
        if name == "":
            coll.update_one({"user_name": user_name}, {
                            "$set": {"email": email, "subjects": subjects, "dept": dept}})
        else:
            coll.update_one({"user_name": user_name}, {
                            "$set": {"name": name, "email": email, "subjects": subjects, "dept": dept}})
    coll = db["faculty"]
    data = list(coll.find({"user_name": user_name}))[0]
    return render_template("edit_profile.html", data=data)


@app.route('/logout', methods=["POST", "GET"])
def logout():
    reload()
    session["id"] = ""
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run(debug=True, port=10000)
