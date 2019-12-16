from flask import render_template, request, redirect, url_for, flash
from flask import session as server_session
from flask_restful import Api
from app import app, api, login_manager, db, firebase
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, CreateIssueForm, CreateProjectForm, AddUserToProjectForm
from app.resources import IssueList, ProjectList, UserList, Issue, Project, UserResource
from app.authentication import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
import requests

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
        email_key = "{}_email".format(int(user_id))
        password_key = "{}_password".format(int(user_id))
        idToken_key = "{}_idToken".format(int(user_id))
        new_idToken = firebase.auth().sign_in_with_email_and_password(server_session[email_key], server_session[password_key])["idToken"]
        server_session[idToken_key] = new_idToken
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

        to_login = User(firebase_user_auth["idToken"], user_id)
        email_key = "{}_email".format(user_id)
        password_key = "{}_password".format(user_id)
        idToken_key = "{}_idToken".format(user_id)
        server_session[email_key] = form.email.data
        server_session[password_key] = form.password.data
        server_session[idToken_key] = firebase_user_auth["idToken"]
        #print("Stored Token: ", server_session[idToken_key])
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
    email_key = "{}_email".format(int(current_user.get_id()))
    password_key = "{}_password".format(int(current_user.get_id()))
    idToken_key = "{}_idToken".format(int(current_user.get_id()))
    server_session.pop(email_key, None)
    server_session.pop(password_key, None)
    server_session.pop(idToken_key, None)
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

@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    idToken = current_user.firebase_token

    if current_user.is_admin():
        projects = db.child("Projects").get(token=idToken).each()
        users = db.child("Users").get(token=idToken).each()
    else:
        all_projects = db.child("Projects").get(token=idToken).each()
        projects = []
        users = []
        for current in all_projects:
            if int(current_user.get_id()) in list(db.child("Projects").child(current.key()).child("Assignees").get(token=idToken).val()):
                projects.append(current)

    project_choices = []
    project_choices_2 = []
    for x in range(len(projects)):
        projects[x] = projects[x].key()
        project_choices.append(tuple([projects[x], db.child("Projects").child(projects[x]).child("Name").get(token=idToken).val()]))
        project_choices_2.append(tuple([projects[x], db.child("Projects").child(projects[x]).child("Name").get(token=idToken).val()]))

    user_choices = []
    for x in range(len(users)):
        users[x] = users[x].key()
        first_name = db.child("Users").child(users[x]).child("First Name").get(token=idToken).val()
        last_name = db.child("Users").child(users[x]).child("Last Name").get(token=idToken).val()
        user_type = db.child("Users").child(users[x]).child("Type").get(token=idToken).val()
        text = "{} {} ({})".format(first_name, last_name, user_type)
        user_choices.append(tuple([users[x], text]))
    
    create_issue = CreateIssueForm()
    create_issue.project.choices = project_choices
    create_project = CreateProjectForm()
    add_user_to_project = AddUserToProjectForm()
    add_user_to_project.project_to_add_to.choices = project_choices_2
    add_user_to_project.user_to_add.choices = user_choices
    if request.method == "POST":
        try:
            if create_issue.submit_issue.data and create_issue.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                new_issue_request = {
                    "name": create_issue.name.data,
                    "description": create_issue.description.data,
                    "priority": create_issue.priority.data,
                    "idToken": server_session[idToken_key]
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 4]
                full_url = "{}{}".format(base_url_trimmed, api.url_for(IssueList)[1:])
                response = requests.post(full_url, json=new_issue_request)
                add_issue_to_project_request = {
                    "idToken": server_session[idToken_key],
                    "id": response.content.decode()[7:len(response.content.decode()) - 2],
                    "type": "issue"
                }
                endpoint = "/{}".format(create_issue.project.data)
                full_url = "{}{}{}".format(base_url_trimmed, api.url_for(ProjectList)[1:], endpoint)
                response = requests.post(full_url, json=add_issue_to_project_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully added new issue to project.")
                else:
                    message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
                    flash(message)
            elif create_project.submit_project.data and create_project.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                new_project_request = {
                    "name": create_project.name.data,
                    "description": create_project.description.data,
                    "begin_date": str(create_project.begin_date.data),
                    "end_date": str(create_project.end_date.data),
                    "idToken": server_session[idToken_key]
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 4]
                full_url = "{}{}".format(base_url_trimmed, api.url_for(ProjectList)[1:])
                response = requests.post(full_url, json=new_project_request)
                new_project_id = response.content.decode()[7:len(response.content.decode()) - 2]
                create_issue.project.choices.append(tuple([int(new_project_id), db.child("Projects").child(int(new_project_id)).child("Name").get(token=server_session[idToken_key]).val()]))
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully created new project.")
                else:
                    message = "Unsuccessful in creating new project. Status Code: {}".format(response.status_code)
                    flash(message)
            elif add_user_to_project.submit_add_user.data and add_user_to_project.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                add_user_request = {
                    "idToken": server_session[idToken_key],
                    "id": add_user_to_project.user_to_add.data,
                    "type": "user"
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 4]
                endpoint = "/{}".format(add_user_to_project.project_to_add_to.data)
                full_url = "{}{}{}".format(base_url_trimmed, api.url_for(ProjectList)[1:], endpoint)
                response = requests.post(full_url, json=add_user_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully added user to project.")
                else:
                    message = "Unsuccessful in adding user to project. Status Code: {}".format(response.status_code)
                    flash(message)
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_admin():
        return render_template("home_template.html", title="Home", create_issue=create_issue, create_project=create_project, add_user=add_user_to_project)
    else:
        return render_template("home_template.html", title="Home", create_issue=create_issue)