from flask_wtf import FlaskForm
from flask import flash, request
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import date
import requests
from app.data import IssueData

class LoginForm(FlaskForm):
    """
    Used for the purposes of logging in users.
    """
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")

class RegistrationForm(FlaskForm):
    """
    Used for the purposes of creating new user accounts.
    """
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password_copy = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    type = SelectField("Type", validators=[DataRequired()], choices=[("developer", "Developer"), ("client", "Client")])
    submit = SubmitField("Register")

class CreateIssueForm(FlaskForm):
    """
    Used for the purposes of creating a new Issue and adding it to a specific Project.
    """
    issue_name = StringField("Issue Name", validators=[DataRequired()])
    issue_description = StringField("Issue Description", validators=[DataRequired()])
    priority = SelectField("Issue Priority", coerce=int, validators=[DataRequired()], choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"), (10, "10")])

    project = SelectField("Project", validators=[DataRequired()])
    submit_issue = SubmitField("Create New Issue")

def handle_create_issue(idToken, create_issue, base_url, issue_list_url, project_list_url):
    new_issue_request = {
        "name": create_issue.issue_name.data,
        "description": create_issue.issue_description.data,
        "priority": create_issue.priority.data,
        "idToken": idToken
    }
    #base_url_trimmed = base_url[:len(base_url) - 4]
    #print("Base URL Trimmed: ", base_url_trimmed)
    #print("Issue List URL: ", issue_list_url[1:])
    full_url = "{}{}".format(request.host_url, "issues")
    response = requests.post(full_url, json=new_issue_request)
    add_issue_to_project_request = {
        "idToken": idToken,
        "id": response.content.decode()[7:len(response.content.decode()) - 2],
        "type": "issue"
    }
    #endpoint = "/{}".format(create_issue.project.data)
    #print("Endpoint: ", endpoint)
    #print("Project List URL: ", project_list_url[1:])
    full_url = "{}{}/{}".format(request.host_url, "projects", create_issue.project.data)
    response = requests.post(full_url, json=add_issue_to_project_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully added new issue to project.")
    else:
        message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
        flash(message)

class ClientCreateIssueForm(FlaskForm):
    """
    Used for the purposes of creating a new Issue, used by Clients.
    """
    name = StringField("Issue Name", validators=[DataRequired()])
    description = StringField("Issue Description", validators=[DataRequired()])
    priority = SelectField("Issue Priority", coerce=int, validators=[DataRequired()], choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"), (10, "10")])
    submit_issue = SubmitField("Create New Issue")

def handle_client_create_issue(idToken, create_issue, base_url, project_choices, issue_list_url, project_list_url):
    new_issue_request = {
        "name": create_issue.name.data,
        "description": create_issue.description.data,
        "priority": create_issue.priority.data,
        "idToken": idToken
    }
    #base_url_trimmed = base_url[:len(base_url) - 4]
    full_url = "{}{}".format(request.host_url, "issues")
    response = requests.post(full_url, json=new_issue_request)
    add_issue_to_project_request = {
        "idToken": idToken,
        "id": response.content.decode()[7:len(response.content.decode()) - 2],
        "type": "issue"
    }
    #endpoint = "/{}".format(project_choices[0][0])
    full_url = "{}{}/{}".format(request.host_url, "projects", project_choices[0][0])
    response = requests.post(full_url, json=add_issue_to_project_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully added new issue to project.")
    else:
        message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
        flash(message)

def handle_project_create_issue(idToken, create_project_issue, base_url, project_data, project_issues, issues, issue_url, host_url):
    new_issue_request = {
        "name": create_project_issue.name.data,
        "description": create_project_issue.description.data,
        "priority": create_project_issue.priority.data,
        "idToken": idToken
    }
    #base_url_trimmed = base_url[:len(base_url) - 15]
    full_url = "{}{}".format(request.host_url, issue_url[1:])
    response = requests.post(full_url, json=new_issue_request)
    add_issue_to_project_request = {
        "idToken": idToken,
        "id": response.content.decode()[7:len(response.content.decode()) - 2],
        "type": "issue"
    }
    #endpoint = "/{}".format(project_data.project_id)
    full_url = "{}projects/{}".format(request.host_url, project_data.project_id)
    response = requests.post(full_url, json=add_issue_to_project_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully added new issue to project.")
        project_data.update(idToken)
        project_issues.append(IssueData(idToken, int(add_issue_to_project_request["id"]), request.host_url, project_data.project_id))
        issues.append(tuple([int(add_issue_to_project_request["id"]), new_issue_request["name"]]))
    else:
        message = "Unsuccessful in adding new issue to project. Status Code: {}".format(response.status_code)
        flash(message)

class CreateProjectForm(FlaskForm):
    """
    Used for the purposes of creating a new Project.
    """
    project_name = StringField("Project Name", validators=[DataRequired()])
    project_description = StringField("Project Description", validators=[DataRequired()])
    begin_date = DateField("Beginning Date", validators=[DataRequired()], default=date.today)
    end_date = DateField("Ending Date", validators=[DataRequired()], default=date.today)
    submit_project = SubmitField("Create New Project")

def handle_create_project(idToken, create_project, create_issue, base_url, project_list_url):
    new_project_request = {
        "name": create_project.project_name.data,
        "description": create_project.project_description.data,
        "begin_date": str(create_project.begin_date.data),
        "end_date": str(create_project.end_date.data),
        "idToken": idToken
    }
    #base_url_trimmed = base_url[:len(base_url) - 4]
    full_url = "{}{}".format(request.host_url, "projects")
    response = requests.post(full_url, json=new_project_request)
    new_project_id = response.content.decode()[7:len(response.content.decode()) - 2]
    create_issue.project.choices.append(tuple([int(new_project_id), create_project.project_name.data]))
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully created new project.")
    else:
        message = "Unsuccessful in creating new project. Status Code: {}".format(response.status_code)
        flash(message)

class AddUserToProjectForm(FlaskForm):
    """
    Used for the purposes of adding an existing User to a specific Project.
    """
    user_to_add = SelectField("User", validators=[DataRequired()])
    project_to_add_to = SelectField("Project", validators=[DataRequired()])
    submit_add_user = SubmitField("Add User To Project")

def handle_add_user_to_project(idToken, add_user_to_project, base_url, project_list_url):
    add_user_request = {
        "idToken": idToken,
        "id": add_user_to_project.user_to_add.data,
        "type": "user"
    }
    #base_url_trimmed = base_url[:len(base_url) - 4]
    #endpoint = "/{}".format(add_user_to_project.project_to_add_to.data)
    full_url = "{}{}/{}".format(request.host_url, "projects", add_user_to_project.project_to_add_to.data)
    response = requests.post(full_url, json=add_user_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully added user to project.")
    elif response.status_code == 400:
        flash("Error: User is already a member of this project.")
    else:
        message = "Unsuccessful in adding user to project. Status Code: {}".format(response.status_code)
        flash(message)

class SelfAssignToIssueForm(FlaskForm):
    """
    Used by developers to assign themselves to issues from a Project they are a member of.
    """    
    selected_issue = SelectField("Issue", validators=[DataRequired()], coerce=int)
    submit = SubmitField("Self-Assign")

def handle_assign_issue_in_project(idToken, user_id, base_url, selected_issue_data, project_issues):
    add_user_request = {
        "idToken": idToken,
        "id": int(user_id),
        "status": ""
    }
    #base_url_trimmed = base_url[:len(base_url) - 15]
    #endpoint = "/{}".format(selected_issue_data)
    full_url = "{}issues/{}".format(request.host_url, selected_issue_data)
    response = requests.post(full_url, json=add_user_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully assigned to issue.")
        for current_issue in project_issues:
            current_issue.update(idToken)
    elif response.status_code == 400:
        flash("Error: User is already assigned to this issue.")
    else:
        message = "Unsuccessful assigning to issue. Status Code: {}".format(response.status_code)
        flash(message)

def handle_self_assign_to_issue(idToken, user_id, base_url, self_assign, project_issues):
    handle_assign_issue_in_project(idToken, user_id, base_url, self_assign.selected_issue.data, project_issues)

class AddUserToIssueForm(FlaskForm):
    """
    Used by admins to add developers to Issues.
    """
    selected_dev = SelectField("Developer", validators=[DataRequired()], coerce=int)
    selected_issue_to_add = SelectField("Issue", validators=[DataRequired()], coerce=int)
    submit_to_issue = SubmitField("Add Developer To Issue", validators=[DataRequired()])

def handle_add_other_user_in_project(idToken, assign_other, base_url, project_issues):
    handle_assign_issue_in_project(idToken, assign_other.selected_dev.data, base_url, assign_other.selected_issue_to_add.data, project_issues)

class SelfAssignInIssueForm(FlaskForm):
    """
    Used by users to assign themselves to an Issue from within its detail screen.
    """
    submit = SubmitField("Self-Assign")

def handle_issue_forms(idToken, user_id, base_url, issue):
    add_user_request = {
        "idToken": idToken,
        "id": int(user_id),
        "status": ""
    }
    #base_url_trimmed = base_url[:len(base_url) - 18]
    #endpoint = "/{}".format(issue.issue_id)
    full_url = "{}issues/{}".format(request.host_url, issue.issue_id)
    response = requests.post(full_url, json=add_user_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully assigned to issue.")
        issue.update(idToken)
    elif response.status_code == 400:
        flash("Error: User is already assigned to this issue.")
    else:
        message = "Unsuccessful assigning to issue. Status Code: {}".format(response.status_code)
        flash(message)

def handle_self_assign_in_issue(idToken, user_id, base_url, issue):
    handle_issue_forms(idToken, user_id, base_url, issue)

class AddUserToIssueWithinForm(FlaskForm):
    """
    Used by admins to assign other users to an issue from within its detail screen.
    """
    selected_dev = SelectField("Developer", validators=[DataRequired()], coerce=int)
    submit_to_issue = SubmitField("Add Developer To Issue", validators=[DataRequired()])

def handle_add_user_within(idToken, assign_other, base_url, issue):
    handle_issue_forms(idToken, assign_other.selected_dev.data, base_url, issue)

class MarkIssueClosedForm(FlaskForm):
    """
    Used by admins and developers to mark an issue as completed or "CLOSED."
    """
    submit_closed = SubmitField("Close Issue", validators=[DataRequired()])

def handle_mark_issue_closed(idToken, issue):
    change_status_request = {
        "idToken": idToken,
        "id": "",
        "status": "CLOSED"
    }
    full_url = "{}issues/{}".format(request.host_url, issue.issue_id)
    response = requests.post(full_url, json=change_status_request)
    if response.status_code == 201 or response.status_code == 200:
        flash("Successfully closed issue.")
        issue.update(idToken)
    else:
        message = "Unsuccessful closing issue. Status Code: {}".format(response.status_code)
        flash(message)
            