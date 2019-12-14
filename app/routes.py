from flask import render_template, request, redirect, url_for, flash
from flask import session as server_session
from app import app, api, login_manager, db, firebase
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm
from app.resources import IssueList, ProjectList, UserList, Issue, Project, UserResource
from app.authentication import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse

api.add_resource(IssueList, "/issues")
api.add_resource(ProjectList, "/projects")
api.add_resource(UserList, "/users")
api.add_resource(Issue, "/issues/<int:issue_id>")
api.add_resource(Project, "/projects/<int:project_id>")
api.add_resource(UserResource, "/users/<int:user_id>")

@app.route("/")
def index():
    return "Hello World!"

@login_manager.user_loader
def load_user(user_id):
    try:
        new_idToken = firebase.auth().sign_in_with_email_and_password(server_session["{}_email".format(user_id)], server_session["{}_password".format(user_id)])["idToken"]
    except:
        return None
    return User(new_idToken, user_id)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if request.method == "POST":
        form.validate()
        firebase_user_auth = None
        try:
            firebase_user_auth = firebase.auth().sign_in_with_email_and_password(form.email.data, form.password.data)
        except:
            flash("Invalid Login Credentials")
            return redirect(url_for("login"))
        users = db.child("Users").get(firebase_user_auth["idToken"]).each()
        user_id = -1
        for current in users:
            if db.child("Users").child(current.key()).child("Email").get(token=firebase_user_auth["idToken"]).val() == form.email.data:
                user_id = current.key()

        if user_id == -1:
            flash("User Not Found In Database")
            return redirect(url_for("login"))

        if not check_password_hash(db.child("Users").child(user_id).child("Password Hash").get(token=firebase_user_auth["idToken"]).val(), form.password.data):
            flash("Invalid Login Credentials")
            return redirect(url_for("login"))

        to_login = User(firebase_user_auth['idToken'], user_id)
        server_session["{}_email".format(user_id)] = form.email.data
        server_session["{}_password".format(user_id)] = form.password.data
        to_login.is_authenticated = True
        login_user(to_login, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")
        return redirect(next_page)
    return render_template("login_template.html", title="Sign In", form=form)

@app.route("/logout")
def logout():
    current_user.is_authenticated = False
    logout_user()
    flash("Logged Out Successfully.")
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = RegistrationForm()
    if request.method == "POST":
        form.validate()
        firebase.auth().create_user_with_email_and_password(form.email.data, form.password.data)
        firebase_user_auth = firebase.auth().sign_in_with_email_and_password(form.email.data, form.password.data)

        new_id = db.child("NextID").get(token=firebase_user_auth["idToken"]).val()
        db.child("NextID").set(new_id + 1, token=firebase_user_auth["idToken"])

        db.child("Users").child(new_id).child("First Name").set(form.first_name.data, token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("Last Name").set(form.last_name.data, token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("Email").set(form.email.data, token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("Password Hash").set(generate_password_hash(form.password.data), token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("ID").set(new_id, token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("Type").set(form.type.data, token=firebase_user_auth["idToken"])
        db.child("Users").child(new_id).child("Authorized").set("True", token=firebase_user_auth["idToken"])

        flash("Registration Complete. Please log in below:")
        return redirect(url_for("login"))
    return render_template('register_template.html', title="Register", form=form)

@app.route("/home")
@login_required
def home():
    return "Home Page"