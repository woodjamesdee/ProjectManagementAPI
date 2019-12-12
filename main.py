from flask import Flask, render_template, request
from flask_restful import Resource, Api, reqparse
import pyrebase

########################################################
        # Database and Resource Initialization #
########################################################

# Initialize the connection to Firebase
firebaseConfig = {
    "apiKey": "AIzaSyAOt2oJnOJHOLgyFHApNINzAqrtS2B0lcY",
    "authDomain": "projectmanagementapi.firebaseapp.com",
    "databaseURL": "https://projectmanagementapi.firebaseio.com",
    "projectId": "projectmanagementapi",
    "storageBucket": "projectmanagementapi.appspot.com",
    "messagingSenderId": "432840428373",
    "appId": "1:432840428373:web:d4aa71e700009b3bed3ddc",
    "measurementId": "G-FX9PKEDNE6"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# Create the Resources
class Issue(Resource):
    """
    Typically a request or intended item of action, an issue is a collection of information able to be categorized. Issues can be OPEN (in-progress) or CLOSED (complete).

    Fields:

    name: A brief title of this Issue. Ex. "Design main character model"
    description: Any and all supporting information for this Issue. Ex. "Must have a red shirt and blue pants"
    id: An auto-assigned value that serves as a unique identifier for this Issue. Ex. 2048
    assignees: Any and all individuals who are assigned to complete this Issue. Ex. "James"
    priority: The importance of this task as described by the Issue creator. Will be a value from 1-10 inclusive. Ex. "10: Mission Critical"
    labels: A collection of brief descriptions commonly used by Issues. Ex. "bug"
    status: The status of this Issue, whether OPEN or CLOSED.
    """

    def get(self, issue_id):
        entries = db.child("Issues").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        if issue_id not in entry_keys:
            return {"error": "Issue Not Found"}, 404

        name = db.child("Issues").child(issue_id).child("Name").get().val()
        description = db.child("Issues").child(issue_id).child("Description").get().val()
        assignees = db.child("Issues").child(issue_id).child("Assignees").get().val()
        priority = db.child("Issues").child(issue_id).child("Priority").get().val()
        labels = db.child("Issues").child(issue_id).child("Labels").get().val()
        status = db.child("Issues").child(issue_id).child("Status").get().val()

        data = {
            "name": name,
            "description": description,
            "id": issue_id,
            "assignees": assignees,
            "priority": priority,
            "labels": labels,
            "status": status
        }

        return data, 200

class Project(Resource):
    """
    A collection of Issues which are all related by some common purpose. Could also be referred to as a "Milestone." Projects can be OPEN (in-progress) or CLOSED (complete).

    Fields:

    name: A brief title of this Project. Ex. "Sprint 11"
    description: Any and all supporting information for this Project. Ex. "Completing this user interface for the application"
    id: An auto-assigned value that serves as a unique identifier for this Issue. Ex. 4096
    issues: A collection of all the Issues contained within this Project. Stored in the form of Issue IDs.
    begin_date: The date that work on this Project begins. Ex. 9 January 2020
    end_date: The date that work on this Project is projected to be complete. Ex. 8 January 2021
    status: The status of this Project, whether OPEN or CLOSED.
    """

    def get(self, project_id):
        entries = db.child("Projects").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        if project_id not in entry_keys:
            return {"error": "Project Not Found"}, 404

        name = db.child("Projects").child(project_id).child("Name").get().val()
        description = db.child("Projects").child(project_id).child("Description").get().val()
        begin_date = db.child("Projects").child(project_id).child("Begin Date").get().val()
        end_date = db.child("Projects").child(project_id).child("End Date").get().val()
        status = db.child("Projects").child(project_id).child("Status").get().val()

        data = {
            "name": name,
            "description": description,
            "id": project_id,
            "begin_date": begin_date,
            "end_date": end_date,
            "status": status
        }

        return data, 200

class User(Resource):
    """
    An individual who may use the API in some capacity. A User has various permissions depending on the type of User that they are.

    Fields:

    first_name: The first name of this User. Ex. "James"
    last_name: The last name of this User. Ex. "Wood"
    email: The email associated with this User. Ex. "test@test.com"
    password_hash: A hashed version of this User's password.
    id: An auto-assigned value that serves as a unique identifier for this User. Ex. 8192
    type: The type of User, which affects permissions. Types include: admin, client, developer.
    """

    def get(self, user_id):
        entries = db.child("Users").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        if user_id not in entry_keys:
            return {"error": "User Not Found"}, 404

        first_name = db.child("Users").child(user_id).child("First Name").get().val()
        last_name = db.child("Users").child(user_id).child("Last Name").get().val()
        email = db.child("Users").child(user_id).child("Email").get().val()
        user_type = db.child("Users").child(user_id).child("Type").get().val()

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "id": user_id,
            "email": email,
            "user_type": user_type
        }

        return data, 200

class IssueList(Resource):
    """
    A collection of Issues.
    """

    def get(self):
        entries = db.child("Issues").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        return {"ids": entry_keys}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True)
        parser.add_argument("description", required=True)
        parser.add_argument("priority", required=True)

        new_id = db.child("NextID").get().val()
        db.child("NextID").set(new_id + 1)

        args = parser.parse_args()
        db.child("Issues").child(new_id).child("Name").set(args["name"])
        db.child("Issues").child(new_id).child("Description").set(args["description"])
        db.child("Issues").child(new_id).child("Priority").set(args["priority"])
        db.child("Issues").child(new_id).child("ID").set(new_id)
        db.child("Issues").child(new_id).child("Assignees").set("")
        db.child("Issues").child(new_id).child("Labels").set("")
        db.child("Issues").child(new_id).child("Status").set("OPEN")

        return 201

class ProjectList(Resource):
    """
    A collection of Projects.
    """

    def get(self):
        entries = db.child("Projects").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        return {"ids": entry_keys}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True)
        parser.add_argument("description", required=True)
        parser.add_argument("begin_date", required=True)
        parser.add_argument("end_date", required=True)

        new_id = db.child("NextID").get().val()
        db.child("NextID").set(new_id + 1)

        args = parser.parse_args()
        db.child("Projects").child(new_id).child("Name").set(args["name"])
        db.child("Projects").child(new_id).child("Description").set(args["description"])
        db.child("Projects").child(new_id).child("Begin Date").set(args["begin_date"])
        db.child("Projects").child(new_id).child("End Date").set(args["end_date"])
        db.child("Projects").child(new_id).child("ID").set(new_id)
        db.child("Projects").child(new_id).child("Issues").set("")
        db.child("Projects").child(new_id).child("Status").set("OPEN")

        return 201

class UserList(Resource):
    """
    A collection of Users.
    """

    def get(self):
        entries = db.child("Users").get().each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        return {"ids": entry_keys}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("first_name", required=True)
        parser.add_argument("last_name", required=True)
        parser.add_argument("email", required=True)
        parser.add_argument("password_hash", required=True)
        parser.add_argument("type", required=True)

        new_id = db.child("NextID").get().val()
        db.child("NextID").set(new_id + 1)

        args = parser.parse_args()
        db.child("Users").child(new_id).child("First Name").set(args["first_name"])
        db.child("Users").child(new_id).child("Last Name").set(args["last_name"])
        db.child("Users").child(new_id).child("Email").set(args["email"])
        db.child("Users").child(new_id).child("Password Hash").set(args["password_hash"])
        db.child("Users").child(new_id).child("ID").set(new_id)
        db.child("Users").child(new_id).child("Type").set(args["type"])

        return 201

########################################################
            # Flask Initialization #
########################################################

# Initialize Flask and the API
app = Flask(__name__)
api = Api(app)

# Add Resources to the API
api.add_resource(IssueList, "/issues")
api.add_resource(ProjectList, "/projects")
api.add_resource(UserList, "/users")
api.add_resource(Issue, "/issues/<int:issue_id>")
api.add_resource(Project, "/projects/<int:project_id>")
api.add_resource(User, "/users/<int:user_id>")

@app.route("/")
def index():
    return "Hello World!"

if __name__ == "__main__":
    app.run()