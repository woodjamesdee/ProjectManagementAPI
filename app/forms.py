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