from app import db
from flask import request

class Data:
    def update(self, idToken):
        pass

class ProjectData(Data):
    def __init__(self, idToken, project_id, base_url):
        self.project_id = project_id
        self.url = "{}home/projects/{}".format(request.host_url, project_id)
        #print("Project URL: ", self.url)
        self.update(idToken)

    def update(self, idToken):
        self.name = db.child("Projects").child(self.project_id).child("Name").get(token=idToken).val()
        self.start_date = db.child("Projects").child(self.project_id).child("Begin Date").get(token=idToken).val()
        self.end_date = db.child("Projects").child(self.project_id).child("End Date").get(token=idToken).val()
        issues = db.child("Projects").child(int(self.project_id)).child("Issues").get(token=idToken).val()
        completed_issues = 0
        for issue in issues:
            status = db.child("Issues").child(int(issue)).child("Status").get(token=idToken).val()
            if status == "CLOSED":
                completed_issues += 1
        self.issue_count = len(issues)
        try:
            self.issue_percent = int(float(completed_issues) / float(self.issue_count) * 100)
        except:
            self.issue_percent = 0
        assignees = db.child("Projects").child(self.project_id).child("Assignees").get(token=idToken).val()
        self.assignees_array = []
        for assignee in assignees:
            first_name = db.child("Users").child(int(assignee)).child("First Name").get(token=idToken).val()
            last_name = db.child("Users").child(int(assignee)).child("Last Name").get(token=idToken).val()
            user_type = db.child("Users").child(int(assignee)).child("Type").get(token=idToken).val()
            entry = "{} {} ({})".format(first_name, last_name, user_type)
            self.assignees_array.append(entry)
        self.assignees = ""
        for element in self.assignees_array:
            self.assignees = self.assignees + element + ", "
        if len(self.assignees) > 0:
            self.assignees = self.assignees[:len(self.assignees) - 2]

class IssueData(Data):
    def __init__(self, idToken, issue_id, base_url, project_id):
        self.issue_id = issue_id
        self.url = "{}home/projects/{}/{}".format(request.host_url, project_id, issue_id)
        self.project_url = "{}home/projects/{}".format(request.host_url, project_id)
        #print("Issue URL: ", self.url)
        self.update(idToken)

    def update(self, idToken):
        self.name = db.child("Issues").child(self.issue_id).child("Name").get(token=idToken).val()
        self.description = db.child("Issues").child(self.issue_id).child("Description").get(token=idToken).val()
        self.priority = db.child("Issues").child(self.issue_id).child("Priority").get(token=idToken).val()
        self.labels = str(db.child("Issues").child(self.issue_id).child("Labels").get(token=idToken).val())
        assignees = db.child("Issues").child(self.issue_id).child("Assignees").get(token=idToken).val()
        self.assignees_array = []
        for assignee in assignees:
            first_name = db.child("Users").child(int(assignee)).child("First Name").get(token=idToken).val()
            last_name = db.child("Users").child(int(assignee)).child("Last Name").get(token=idToken).val()
            user_type = db.child("Users").child(int(assignee)).child("Type").get(token=idToken).val()
            entry = "{} {} ({})".format(first_name, last_name, user_type)
            self.assignees_array.append(entry)
        self.assignees = ""
        for element in self.assignees_array:
            self.assignees = self.assignees + element + ", "
        if len(self.assignees) > 0:
            self.assignees = self.assignees[:len(self.assignees) - 2]
