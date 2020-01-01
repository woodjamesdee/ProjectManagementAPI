from flask import render_template, request, redirect, url_for, flash
from flask import session as server_session
from flask_restful import Api
from app import app, api, login_manager, db, firebase
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, CreateIssueForm, CreateProjectForm, AddUserToProjectForm, ClientCreateIssueForm, SelfAssignToIssueForm, AddUserToIssueForm, SelfAssignInIssueForm, AddUserToIssueWithinForm, MarkIssueClosedForm
from app.resources import IssueList, ProjectList, UserList, Issue, Project, UserResource
from app.authentication import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
import requests
from app.data import ProjectData, IssueData
from app.helper import get_project_choices, get_user_choices, get_user_issues, get_user_projects, check_project_exists, check_if_user_is_project_member, get_project_issues, get_project_devs, check_issue_exists, check_if_issue_is_project_member

api.add_resource(IssueList, "/issues")
api.add_resource(ProjectList, "/projects")
api.add_resource(UserList, "/users")
api.add_resource(Issue, "/issues/<int:issue_id>")
api.add_resource(Project, "/projects/<int:project_id>")
api.add_resource(UserResource, "/users/<int:user_id>")

@app.route("/")
def index():
    return redirect(url_for("home"))

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
    # Get Authentication Token
    idToken = current_user.firebase_token

    # Get the possible selection choices for various form fields
    project_choices = get_project_choices(idToken)
    user_choices = get_user_choices(idToken)

    # Instantiate the input forms
    create_issue = CreateIssueForm()
    create_issue.project.choices = project_choices
    create_project = CreateProjectForm()
    add_user_to_project = AddUserToProjectForm()
    add_user_to_project.project_to_add_to.choices = project_choices
    add_user_to_project.user_to_add.choices = user_choices
    client_create_issue = ClientCreateIssueForm()

    # If a form has been submitted
    if request.method == "POST":
        try:
            # If the create_issue form has been submitted
            if create_issue.submit_issue.data and create_issue.validate():
                from app.forms import handle_create_issue
                handle_create_issue(idToken, create_issue, request.base_url, api.url_for(IssueList), api.url_for(ProjectList))
            # If the create_project form has been submitted
            elif create_project.submit_project.data and create_project.validate():
                from app.forms import handle_create_project
                handle_create_project(idToken, create_project, create_issue, request.base_url, api.url_for(ProjectList))
            # If the add_user_to_project form has been submitted
            elif add_user_to_project.submit_add_user.data and add_user_to_project.validate():
                from app.forms import handle_add_user_to_project
                handle_add_user_to_project(idToken, add_user_to_project, request.base_url, api.url_for(ProjectList))
            # If the client has submitted an issue
            elif client_create_issue.submit_issue.data and client_create_issue.validate():
                from app.forms import handle_client_create_issue
                handle_client_create_issue(idToken, client_create_issue, request.base_url, project_choices, api.url_for(IssueList), api.url_for(ProjectList))
        except:
                flash("An internal error occurred while processing this request.")

    # Render a page template based upon the user type
    if current_user.is_admin():
        return render_template("admin_home_template.html", title="Home", create_issue=create_issue, create_project=create_project, add_user=add_user_to_project, projects=get_user_projects(idToken, project_choices), issues=get_user_issues(idToken, project_choices))
    elif current_user.is_developer():
        return render_template("dev_home_template.html", title="Home", create_issue=create_issue, projects=get_user_projects(idToken, project_choices), issues=get_user_issues(idToken, project_choices))
    elif current_user.is_client():
        return render_template("client_home_template.html", title="Home", create_issue=client_create_issue, project=get_user_projects(idToken, project_choices))
    else:
        return "Not implemented for unknown user type."

@app.route("/home/projects/<int:project_id>", methods=["GET", "POST"])
@login_required
def project_detail(project_id):
    idToken = current_user.firebase_token

    # Perform required checks to ensure proper access.

    # Check if project exists
    if not check_project_exists(idToken, project_id):
        return {"error": "Project not found!"}, 404
    
    # Check if user is a member of the project
    if not check_if_user_is_project_member(idToken, int(current_user.get_id()), project_id):
        return {"error": "User not member of this project!"}, 401

    # Create Forms and Data

    project_data = ProjectData(idToken, project_id, request.host_url)

    # Obtain a list of all of the project issues
    project_issues, issues = get_project_issues(idToken, project_id)

    # Obtain a list of possible developers to assign issues to
    dev_choices = get_project_devs(idToken, project_id)

    # Instantiate the forms
    create_project_issue = ClientCreateIssueForm()
    self_assign = SelfAssignToIssueForm()
    self_assign.selected_issue.choices = issues
    assign_other = AddUserToIssueForm()
    assign_other.selected_issue_to_add.choices = issues
    assign_other.selected_dev.choices = dev_choices

    # If a form has been submitted
    if request.method == "POST":
        try:
            # If the create issue form has been submitted
            if create_project_issue.submit_issue.data and create_project_issue.validate():
                from app.forms import handle_project_create_issue
                handle_project_create_issue(idToken, create_project_issue, request.base_url, project_data, project_issues, issues, api.url_for(IssueList), request.host_url)
            # If the self assign form has been submitted
            elif self_assign.submit.data and self_assign.validate():
                from app.forms import handle_self_assign_to_issue
                handle_self_assign_to_issue(idToken, current_user.get_id(), request.base_url, self_assign, project_issues)
            # If the assign other form has been submitted
            elif assign_other.submit_to_issue.data and assign_other.validate():
                from app.forms import handle_add_other_user_in_project
                handle_add_other_user_in_project(idToken, assign_other, request.base_url, project_issues)
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_developer():
        return render_template("project_home_template.html", title="Project Home", create_issue=create_project_issue, self_assign=self_assign, project=project_data, issues=project_issues)
    elif current_user.is_admin():
        return render_template("project_home_template.html", title="Project Home", create_issue=create_project_issue, self_assign=self_assign, project=project_data, issues=project_issues, assign_other=assign_other)
    else:
        return "Not implemented for unknown user type."

@app.route("/home/projects/<int:project_id>/<int:issue_id>", methods=["GET", "POST"])
@login_required
def issue_detail(project_id, issue_id):
    idToken = current_user.firebase_token
    # Perform required checks to ensure proper access.

    # Check that issue exists
    if not check_issue_exists(idToken, issue_id):
        return {"error": "Issue not found!"}, 404

    # Check that issue is also a member of this project
    if not check_if_issue_is_project_member(idToken, issue_id, project_id):
        return {"error": "Issue is not included in this project!"}, 401
    
    # Check if the user making the request is a member of this project
    if not check_if_user_is_project_member(idToken, int(current_user.get_id()), project_id):
        return {"error": "User not member of this project!"}, 401

    # Create Forms and Data

    # For the purposes of assigning a user to this issue, get a list of options
    dev_choices = get_project_devs(idToken, project_id)

    # Instantiate Forms and Data
    self_assign = SelfAssignInIssueForm()
    assign_other = AddUserToIssueWithinForm()
    assign_other.selected_dev.choices = dev_choices
    issue = IssueData(idToken, issue_id, request.host_url, project_id)
    close_issue = MarkIssueClosedForm()

    # If a form has been submitted
    if request.method == "POST":
        try:
            # If the self assign form has been submitted
            if self_assign.submit.data and self_assign.validate():
                from app.forms import handle_self_assign_in_issue
                handle_self_assign_in_issue(idToken, current_user.get_id(), request.base_url, issue)
            # If the assign other form ha been submitted
            elif assign_other.submit_to_issue.data and assign_other.validate():
                from app.forms import handle_add_user_within
                handle_add_user_within(idToken, assign_other, request.base_url, issue)
            elif close_issue.submit_closed.data and close_issue.validate():
                from app.forms import handle_mark_issue_closed
                handle_mark_issue_closed(idToken, issue)
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_developer():
        return render_template("issue_home_template.html", title="Issue Home", self_assign=self_assign, issue=issue, close_issue=close_issue)
    elif current_user.is_admin():
        return render_template("issue_home_template.html", title="Issue Home", self_assign=self_assign, issue=issue, assign_other=assign_other, close_issue=close_issue)
    else:
        return "Invalid user type."