from flask import render_template, request, redirect, url_for, flash
from flask import session as server_session
from flask_restful import Api
from app import app, api, login_manager, db, firebase
from flask_login import current_user, login_user, logout_user, login_required
from app.forms import LoginForm, RegistrationForm, CreateIssueForm, CreateProjectForm, AddUserToProjectForm, ClientCreateIssueForm, SelfAssignToIssueForm, AddUserToIssueForm, SelfAssignInIssueForm, AddUserToIssueWithinForm
from app.resources import IssueList, ProjectList, UserList, Issue, Project, UserResource
from app.authentication import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse
import requests
from app.data import ProjectData, IssueData

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
    client_create_issue = ClientCreateIssueForm()
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
            elif client_create_issue.submit_issue.data and client_create_issue.validate():
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
                endpoint = "/{}".format(project_choices[0][0])
                full_url = "{}{}{}".format(base_url_trimmed, api.url_for(ProjectList)[1:], endpoint)
                response = requests.post(full_url, json=add_issue_to_project_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully added new issue to project.")
                else:
                    message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
                    flash(message)
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_admin():
        projs = []
        for current_project in project_choices:
            projs.append(ProjectData(idToken, current_project[0], request.host_url))
        admin_issues = []
        #for current_project in project_choices:
        #    admin_issues.append(IssueData(idToken, current_project[0], request.host_url))
        issues = db.child("Issues").get(token=idToken).each()
        for issue in issues:
            issue_key = int(issue.key())
            if isinstance(db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val(), list):
                if int(current_user.get_id()) in db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val():
                    admin_issues.append(IssueData(idToken, issue_key, request.host_url, project_choices[0][0]))
        return render_template("admin_home_template.html", title="Home", create_issue=create_issue, create_project=create_project, add_user=add_user_to_project, projects=projs, issues=admin_issues)
    elif current_user.is_client():
        if len(project_choices) > 0:
            project = ProjectData(idToken, project_choices[0][0], request.host_url)
        else:
            project = None
        return render_template("client_home_template.html", title="Home", create_issue=client_create_issue, project=project)
    elif current_user.is_developer():
        dev_projects = []
        dev_issues = []
        for current_project in project_choices:
            dev_projects.append(ProjectData(idToken, current_project[0], request.host_url))
        issues = db.child("Issues").get(token=idToken).each()
        for issue in issues:
            issue_key = int(issue.key())
            if isinstance(db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val(), list):
                if int(current_user.get_id()) in db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val():
                    dev_issues.append(IssueData(idToken, issue_key, request.host_url, project_choices[0][0]))

        return render_template("dev_home_template.html", title="Home", create_issue=create_issue, projects=dev_projects, issues=dev_issues)
    else:
        return render_template("home_template.html", title="Home", create_issue=create_issue)

@app.route("/home/projects/<int:project_id>", methods=["GET", "POST"])
@login_required
def project_detail(project_id):
    idToken = current_user.firebase_token
    if db.child("Projects").child(project_id).get(token=idToken).val() is None:
        return {"error": "Project not found!"}, 404
    
    project_assignees = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
    if not current_user.is_admin():
        if not isinstance(project_assignees, list) or int(current_user.get_id()) not in project_assignees:
            return {"error": "User not member of this project!"}, 401

    project_data = ProjectData(idToken, project_id, request.host_url)
    issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()
    project_issues = []
    if not isinstance(issues, list):
        project_issues = None
    else:
        for issue in issues:
            project_issues.append(IssueData(idToken, issue, request.host_url, project_id))

    for x in range(len(issues)):
        issues[x] = tuple([issues[x], db.child("Issues").child(issues[x]).child("Name").get(token=idToken).val()])

    dev_choices = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
    if not isinstance(dev_choices, list):
        dev_choices = None
    else:
        for x in range(len(dev_choices)):
            first_name = db.child("Users").child(dev_choices[x]).child("First Name").get(token=idToken).val()
            last_name = db.child("Users").child(dev_choices[x]).child("Last Name").get(token=idToken).val()
            user_type = db.child("Users").child(dev_choices[x]).child("Type").get(token=idToken).val()
            entry = "{}{} ({})".format(first_name, last_name, user_type)
            dev_choices[x] = tuple([dev_choices[x], entry])

    create_project_issue = ClientCreateIssueForm()
    self_assign = SelfAssignToIssueForm()
    self_assign.selected_issue.choices = issues
    assign_other = AddUserToIssueForm()
    assign_other.selected_issue_to_add.choices = issues
    assign_other.selected_dev.choices = dev_choices

    if request.method == "POST":
        try:
            if create_project_issue.submit_issue.data and create_project_issue.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                new_issue_request = {
                    "name": create_project_issue.name.data,
                    "description": create_project_issue.description.data,
                    "priority": create_project_issue.priority.data,
                    "idToken": server_session[idToken_key]
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 15]
                full_url = "{}{}".format(base_url_trimmed, api.url_for(IssueList)[1:])
                response = requests.post(full_url, json=new_issue_request)
                add_issue_to_project_request = {
                    "idToken": server_session[idToken_key],
                    "id": response.content.decode()[7:len(response.content.decode()) - 2],
                    "type": "issue"
                }
                endpoint = "/{}".format(project_id)
                full_url = "{}projects{}".format(base_url_trimmed, endpoint)
                response = requests.post(full_url, json=add_issue_to_project_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully added new issue to project.")
                    project_data.update(idToken)
                    #for current_issue in project_issues:
                    #    current_issue.update(idToken)
                    project_issues.append(IssueData(idToken, int(add_issue_to_project_request["id"]), request.host_url, project_id))
                    issues.append(tuple([int(add_issue_to_project_request["id"]), new_issue_request["name"]]))
                else:
                    message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
                    flash(message)
            elif self_assign.submit.data and self_assign.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                add_user_request = {
                    "idToken": server_session[idToken_key],
                    "id": int(current_user.get_id()),
                    "type": "user"
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 15]
                endpoint = "/{}".format(self_assign.selected_issue.data)
                full_url = "{}issues{}".format(base_url_trimmed, endpoint)
                response = requests.post(full_url, json=add_user_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully self-assigned to issue.")
                    for current_issue in project_issues:
                        current_issue.update(idToken)
                else:
                    message = "Unsuccessful self-assigning to issue. Status Code: {}".format(response.status_code)
                    flash(message)
            elif assign_other.submit_to_issue.data and assign_other.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                add_user_request = {
                    "idToken": server_session[idToken_key],
                    "id": assign_other.selected_dev.data,
                    "type": "user"
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 15]
                endpoint = "/{}".format(assign_other.selected_issue_to_add.data)
                full_url = "{}issues{}".format(base_url_trimmed, endpoint)
                response = requests.post(full_url, json=add_user_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully assigned user to issue.")
                    for current_issue in project_issues:
                        current_issue.update(idToken)
                else:
                    message = "Unsuccessful in assigning user to issue. Status Code: {}".format(response.status_code)
            
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_client():
        return "Not implemented"
    elif current_user.is_developer():
        return render_template("project_home_template.html", title="Project Home", create_issue=create_project_issue, self_assign=self_assign, project=project_data, issues=project_issues)
    elif current_user.is_admin():
        return render_template("project_home_template.html", title="Project Home", create_issue=create_project_issue, self_assign=self_assign, project=project_data, issues=project_issues, assign_other=assign_other)
    else:
        return "Invalid user type."

@app.route("/home/projects/<int:project_id>/<int:issue_id>", methods=["GET", "POST"])
@login_required
def issue_detail(project_id, issue_id):
    idToken = current_user.firebase_token
    if db.child("Issues").child(issue_id).get(token=idToken).val() is None:
        return {"error": "Issue not found!"}, 404

    project_issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()
    if not current_user.is_admin():
        if not isinstance(project_issues, list) or issue_id not in project_issues:
            return {"error": "Issue is not included in this project!"}, 401
    
    project_assignees = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
    if not current_user.is_admin():
        if not isinstance(project_assignees, list) or int(current_user.get_id()) not in project_assignees:
            return {"error": "User not member of this project!"}, 401

    dev_choices = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
    if not isinstance(dev_choices, list):
        dev_choices = None
    else:
        for x in range(len(dev_choices)):
            first_name = db.child("Users").child(dev_choices[x]).child("First Name").get(token=idToken).val()
            last_name = db.child("Users").child(dev_choices[x]).child("Last Name").get(token=idToken).val()
            user_type = db.child("Users").child(dev_choices[x]).child("Type").get(token=idToken).val()
            entry = "{}{} ({})".format(first_name, last_name, user_type)
            dev_choices[x] = tuple([dev_choices[x], entry])

    self_assign = SelfAssignInIssueForm()
    assign_other = AddUserToIssueWithinForm()
    assign_other.selected_dev.choices = dev_choices

    issue = IssueData(idToken, issue_id, request.host_url, project_id)

    if request.method == "POST":
        try:
            if self_assign.submit.data and self_assign.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                add_user_request = {
                    "idToken": server_session[idToken_key],
                    "id": int(current_user.get_id()),
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 18]
                endpoint = "/{}".format(issue_id)
                full_url = "{}issues{}".format(base_url_trimmed, endpoint)
                response = requests.post(full_url, json=add_user_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully self-assigned to issue.")
                    issue.update(idToken)
                else:
                    message = "Unsuccessful self-assigning to issue. Status Code: {}".format(response.status_code)
                    flash(message)
            elif assign_other.submit_to_issue.data and assign_other.validate():
                idToken_key = "{}_idToken".format(int(current_user.get_id()))
                add_user_request = {
                    "idToken": server_session[idToken_key],
                    "id": assign_other.selected_dev.data,
                }
                base_url_trimmed = request.base_url[:len(request.base_url) - 18]
                endpoint = "/{}".format(issue_id)
                full_url = "{}issues{}".format(base_url_trimmed, endpoint)
                response = requests.post(full_url, json=add_user_request)
                if response.status_code == 201 or response.status_code == 200:
                    flash("Successfully assigned user to issue.")
                    issue.update(idToken)
                else:
                    message = "Unsuccessful in assigning user to issue. Status Code: {}".format(response.status_code)
            
        except:
                flash("An internal error occurred while processing this request.")

    if current_user.is_client():
        return "Not implemented"
    elif current_user.is_developer():
        return render_template("issue_home_template.html", title="Issue Home", self_assign=self_assign, issue=issue)
    elif current_user.is_admin():
        return render_template("issue_home_template.html", title="Issue Home", self_assign=self_assign, issue=issue, assign_other=assign_other)
    else:
        return "Invalid user type."