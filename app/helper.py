from app import db
from flask_login import current_user
from flask import request
from app.data import ProjectData, IssueData

def get_project_choices(idToken):
    if current_user.is_admin():
        projects = db.child("Projects").get(token=idToken).each()
        if projects is None:
            projects = []
    else:
        all_projects = db.child("Projects").get(token=idToken).each()
        projects = []
        if all_projects is not None:
            for current in all_projects:
                if int(current_user.get_id()) in list(db.child("Projects").child(current.key()).child("Assignees").get(token=idToken).val()):
                    projects.append(current)

    project_choices = []
    for x in range(len(projects)):
        projects[x] = projects[x].key()
        project_choices.append(tuple([projects[x], db.child("Projects").child(projects[x]).child("Name").get(token=idToken).val()]))

    return project_choices

def get_user_choices(idToken):
    if current_user.is_admin():
        users = db.child("Users").get(token=idToken).each()
    else:
        return []
    
    user_choices = []
    for x in range(len(users)):
        users[x] = users[x].key()
        first_name = db.child("Users").child(users[x]).child("First Name").get(token=idToken).val()
        last_name = db.child("Users").child(users[x]).child("Last Name").get(token=idToken).val()
        user_type = db.child("Users").child(users[x]).child("Type").get(token=idToken).val()
        text = "{} {} ({})".format(first_name, last_name, user_type)
        user_choices.append(tuple([users[x], text]))

    return user_choices

def get_user_issues(idToken, project_choices, open_only=True):
    if current_user.is_admin():
        admin_issues = []
        issues = db.child("Issues").get(token=idToken).each()
        if issues is None:
            issues = []
        for issue in issues:
            issue_key = int(issue.key())
            if isinstance(db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val(), list):
                if int(current_user.get_id()) in db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val():
                    all_projects = db.child("Projects").get(token=idToken).each()
                    project_id = -1
                    for project in all_projects:
                        if issue_key in project.val()["Issues"]:
                            project_id = int(project.key())
                            break
                    if not open_only:
                        admin_issues.append(IssueData(idToken, issue_key, request.host_url, project_id))
                    elif db.child("Issues").child(issue_key).child("Status").get(token=idToken).val() == "OPEN":
                        admin_issues.append(IssueData(idToken, issue_key, request.host_url, project_id))
        return admin_issues
    elif current_user.is_developer():
        dev_issues = []
        issues = db.child("Issues").get(token=idToken).each()
        if issues is None:
            issues = []
        for issue in issues:
            issue_key = int(issue.key())
            if isinstance(db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val(), list):
                if int(current_user.get_id()) in db.child("Issues").child(issue_key).child("Assignees").get(token=idToken).val():
                    if not open_only:
                        dev_issues.append(IssueData(idToken, issue_key, request.host_url, project_choices[0][0]))
                    elif db.child("Issues").child(issue_key).child("Status").get(token=idToken).val() == "OPEN":
                        dev_issues.append(IssueData(idToken, issue_key, request.host_url, project_choices[0][0]))
        return dev_issues
    else:
        return None

def get_user_projects(idToken, project_choices):
    if current_user.is_admin():
        projs = []
        for current_project in project_choices:
            projs.append(ProjectData(idToken, current_project[0], request.host_url))
        return projs
    elif current_user.is_client():
        if len(project_choices) > 0:
            project = ProjectData(idToken, project_choices[0][0], request.host_url)
        else:
            project = None
        return project
    elif current_user.is_developer():
        dev_projects = []
        for current_project in project_choices:
            dev_projects.append(ProjectData(idToken, current_project[0], request.host_url))
        return dev_projects

def check_project_exists(idToken, project_id):
    if db.child("Projects").child(project_id).get(token=idToken).val() is None:
        return False
    return True

def check_if_user_is_project_member(idToken, user_id, project_id):
    if current_user.is_admin():
        return True
    else:
        project_assignees = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
        if not isinstance(project_assignees, list) or user_id not in project_assignees:
            return False
        return True

def get_project_issues(idToken, project_id, open_only=True):
    all_issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()
    issues = []
    project_issues = []
    if not isinstance(issues, list):
        project_issues = []
        issues = []
    else:
        if open_only:
            for current_issue in all_issues:
                if db.child("Issues").child(current_issue).child("Status").get(token=idToken).val() == "OPEN":
                    issues.append(current_issue)
        for issue in issues:
            project_issues.append(IssueData(idToken, issue, request.host_url, project_id))
    for x in range(len(issues)):
        issues[x] = tuple([issues[x], db.child("Issues").child(issues[x]).child("Name").get(token=idToken).val()])
    return project_issues, issues

def get_project_devs(idToken, project_id):
    all_dev_choices = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
    if not isinstance(all_dev_choices, list):
        all_dev_choices = []
    dev_choices = []
    for choice in all_dev_choices:
        if db.child("Users").child(choice).child("Type").get(token=idToken).val() in ["admin", "developer"]:
            dev_choices.append(choice)
    else:
        for x in range(len(dev_choices)):
            first_name = db.child("Users").child(dev_choices[x]).child("First Name").get(token=idToken).val()
            last_name = db.child("Users").child(dev_choices[x]).child("Last Name").get(token=idToken).val()
            user_type = db.child("Users").child(dev_choices[x]).child("Type").get(token=idToken).val()
            entry = "{} {} ({})".format(first_name, last_name, user_type)
            dev_choices[x] = tuple([dev_choices[x], entry])
    return dev_choices

def check_issue_exists(idToken, issue_id):
    if db.child("Issues").child(issue_id).get(token=idToken).val() is None:
        return False
    return True

def check_if_issue_is_project_member(idToken, issue_id, project_id):
    project_issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()
    if not isinstance(project_issues, list) or issue_id not in project_issues:
        return False
    return True