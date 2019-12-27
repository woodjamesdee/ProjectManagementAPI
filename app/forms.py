from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import date

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
    name = StringField("Issue Name", validators=[DataRequired()])
    description = StringField("Issue Description", validators=[DataRequired()])
    priority = SelectField("Issue Priority", coerce=int, validators=[DataRequired()], choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"), (10, "10")])

    project = SelectField("Project", validators=[DataRequired()])
    submit_issue = SubmitField("Create New Issue")

class ClientCreateIssueForm(FlaskForm):
    """
    Used for the purposes of creating a new Issue, used by Clients.
    """
    name = StringField("Issue Name", validators=[DataRequired()])
    description = StringField("Issue Description", validators=[DataRequired()])
    priority = SelectField("Issue Priority", coerce=int, validators=[DataRequired()], choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"), (10, "10")])
    submit_issue = SubmitField("Create New Issue")

class CreateProjectForm(FlaskForm):
    """
    Used for the purposes of creating a new Project.
    """
    name = StringField("Project Name", validators=[DataRequired()])
    description = StringField("Project Description", validators=[DataRequired()])
    begin_date = DateField("Beginning Date", validators=[DataRequired()], default=date.today)
    end_date = DateField("Ending Date", validators=[DataRequired()], default=date.today)
    submit_project = SubmitField("Create New Project")

class AddUserToProjectForm(FlaskForm):
    """
    Used for the purposes of adding an existing User to a specific Project.
    """
    user_to_add = SelectField("User", validators=[DataRequired()], coerce=int)
    project_to_add_to = SelectField("Project", validators=[DataRequired()])
    submit_add_user = SubmitField("Add User To Project")

class SelfAssignToIssueForm(FlaskForm):
    """
    Used by developers to assign themselves to issues from a Project they are a member of.
    """    
    selected_issue = SelectField("Issue", validators=[DataRequired()], coerce=int)
    submit = SubmitField("Self-Assign")

class AddUserToIssueForm(FlaskForm):
    """
    Used by admins to add developers to Issues.
    """
    selected_dev = SelectField("Developer", validators=[DataRequired()], coerce=int)
    selected_issue_to_add = SelectField("Issue", validators=[DataRequired()], coerce=int)
    submit_to_issue = SubmitField("Add Developer To Issue", validators=[DataRequired()])

class SelfAssignInIssueForm(FlaskForm):
    """
    Used by users to assign themselves to an Issue from within its detail screen.
    """
    submit = SubmitField("Self-Assign")

class AddUserToIssueWithinForm(FlaskForm):
    """
    Used by admins to assign other users to an issue from within its detail screen.
    """
    selected_dev = SelectField("Developer", validators=[DataRequired()], coerce=int)
    submit_to_issue = SubmitField("Add Developer To Issue", validators=[DataRequired()])