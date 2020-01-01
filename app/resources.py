from app import db, firebase
from flask_restful import Resource, reqparse
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from flask import session as server_session
from flask import request

class CredResource(Resource):
    pass

class Issue(CredResource):
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

    def post(self, issue_id):
        parser = reqparse.RequestParser()
        parser.add_argument("idToken", required=True)
        parser.add_argument("id", required=True)
        parser.add_argument("status", required=True)
        args = parser.parse_args()
        idToken = args["idToken"]
        entries = db.child("Issues").get(token=idToken).each()
        entry_keys = []
        
        for entry in entries:
            entry_keys.append(entry.key())

        if str(issue_id) not in entry_keys and issue_id not in entry_keys:
            return {"error": "Issue Not Found"}, 404

        if args["id"] == "" and args["status"] == "":

            name = db.child("Issues").child(issue_id).child("Name").get(token=idToken).val()
            description = db.child("Issues").child(issue_id).child("Description").get(token=idToken).val()
            assignees = db.child("Issues").child(issue_id).child("Assignees").get(token=idToken).val()
            priority = db.child("Issues").child(issue_id).child("Priority").get(token=idToken).val()
            labels = db.child("Issues").child(issue_id).child("Labels").get(token=idToken).val()
            status = db.child("Issues").child(issue_id).child("Status").get(token=idToken).val()

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
        elif args["status"] == "":
            current_users = db.child("Issues").child(issue_id).child("Assignees").get(token=idToken).val()
            if current_users is None or current_users == "":
                current_users = [int(args["id"])]
            elif int(args["id"]) in current_users:
                return {"error": "User already assigned to issue."}, 400
            else:
                current_users.append(int(args["id"]))
            db.child("Issues").child(issue_id).child("Assignees").set(current_users, token=idToken)
        else:
            new_status = args["status"]
            db.child("Issues").child(issue_id).child("Status").set(new_status, token=idToken)
        return 201

        

class Project(CredResource):
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
    assignees: The individual Users who are members of this Project.
    """
    def post(self, project_id):
        parser = reqparse.RequestParser()
        parser.add_argument("id", required=True)   
        parser.add_argument("type", required=True) 
        parser.add_argument("idToken", required=True)
        args = parser.parse_args()
        idToken = args["idToken"]
        entries = db.child("Projects").get(token=idToken).each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(str(entry.key()))

        if str(project_id) not in entry_keys and project_id not in entry_keys:
            print("Project not found!")
            print("Project ID: ", project_id)
            return {"error": "Project Not Found"}, 404

        if args["id"] == "" and args["type"] == "":
            # Treat as a GET request
            name = db.child("Projects").child(project_id).child("Name").get(token=idToken).val()
            description = db.child("Projects").child(project_id).child("Description").get(token=idToken).val()
            begin_date = db.child("Projects").child(project_id).child("Begin Date").get(token=idToken).val()
            end_date = db.child("Projects").child(project_id).child("End Date").get(token=idToken).val()
            status = db.child("Projects").child(project_id).child("Status").get(token=idToken).val()
            assignees = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
            issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()

            data = {
                "name": name,
                "description": description,
                "id": project_id,
                "begin_date": begin_date,
                "end_date": end_date,
                "status": status,
                "assignees": assignees,
                "issues": issues
            }

            return {"data": data} , 200

        request_type = args["type"]
        if request_type == "user":
            current_users = db.child("Projects").child(project_id).child("Assignees").get(token=idToken).val()
            if current_users is None or current_users == "":
                current_users = [int(args["id"])]
            elif int(args["id"]) in current_users:
                return {"error": "User already a member of this project."}, 400
            else:
                current_users.append(int(args["id"]))
            db.child("Projects").child(project_id).child("Assignees").set(current_users, token=idToken)
        elif request_type == "issue":
            current_issues = db.child("Projects").child(project_id).child("Issues").get(token=idToken).val()
            if current_issues is None or current_issues == "":
                current_issues = [int(args["id"])]
            elif int(args["id"]) in current_issues:
                return {"error": "Issue already a member of this project."}, 400
            else:
                current_issues.append(int(args["id"]))
            db.child("Projects").child(project_id).child("Issues").set(current_issues, token=idToken)
        else:
            return {"error": "Bad ID Type"}, 400
        
        return 201


class UserResource(CredResource):
    """
    An individual who may use the API in some capacity. A User has various permissions depending on the type of User that they are.

    Fields:

    first_name: The first name of this User. Ex. "James"
    last_name: The last name of this User. Ex. "Wood"
    email: The email associated with this User. Ex. "test@test.com"
    password_hash: A hashed version of this User's password.
    id: An auto-assigned value that serves as a unique identifier for this User. Ex. 8192
    type: The type of User, which affects permissions. Types include: admin, client, developer.
    authorized: If the user is currently logged in (authorized). Ex. "True"
    """

    def post(self, user_id):
        parser = reqparse.RequestParser()
        parser.add_argument("idToken", required=True)
        args = parser.parse_args()
        idToken = args["idToken"]
        entries = db.child("Users").get(token=idToken).each()
        entry_keys = []
        for entry in entries:
            entry_keys.append(entry.key())

        if user_id not in entry_keys and str(user_id) not in entry_keys:
            return {"error": "User Not Found"}, 404

        first_name = db.child("Users").child(user_id).child("First Name").get(token=idToken).val()
        last_name = db.child("Users").child(user_id).child("Last Name").get(token=idToken).val()
        email = db.child("Users").child(user_id).child("Email").get(token=idToken).val()
        user_type = db.child("Users").child(user_id).child("Type").get(token=idToken).val()
        authorized = db.child("Users").child(user_id).child("Authorized").get(token=idToken).val()

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "id": user_id,
            "email": email,
            "user_type": user_type,
            "authorized": authorized
        }

        return {"data": data}, 200

class IssueList(CredResource):
    """
    A collection of Issues.
    """
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", required=True)
        parser.add_argument("description", required=True)
        parser.add_argument("priority", required=True)
        parser.add_argument("idToken", required=True)

        args = parser.parse_args()

        idToken = args["idToken"]
        
        if args["name"] == "" and args["description"] == "" and args["priority"] == "":
            # Treat as a GET request where only idToken is passed for authentication.
            entries = db.child("Issues").get(token=idToken).each()
            entry_keys = []
            for entry in entries:
                entry_keys.append(entry.key())

            return {"ids": entry_keys}, 200

        new_id = db.child("NextID").get(token=idToken).val()
        db.child("NextID").set((new_id + 1), token=idToken)

        
        db.child("Issues").child(new_id).child("Name").set(args["name"], token=idToken)
        db.child("Issues").child(new_id).child("Description").set(args["description"], token=idToken)
        db.child("Issues").child(new_id).child("Priority").set(args["priority"], token=idToken)
        db.child("Issues").child(new_id).child("ID").set(new_id, token=idToken)
        db.child("Issues").child(new_id).child("Assignees").set("", token=idToken)
        db.child("Issues").child(new_id).child("Labels").set("", token=idToken)
        db.child("Issues").child(new_id).child("Status").set("OPEN", token=idToken)

        return {"id": new_id}, 201

class ProjectList(CredResource):
    """
    A collection of Projects.
    """
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("idToken", required=True)
        parser.add_argument("name", required=True)
        parser.add_argument("description", required=True)
        parser.add_argument("begin_date", required=True)
        parser.add_argument("end_date", required=True)

        args = parser.parse_args()
        idToken = args["idToken"]

        if args["name"] == "" and args["description"] == "" and args["begin_date"] == "" and args["end_date"] == "":
            # Treat as a GET request
            entries = db.child("Projects").get(token=idToken).each()
            entry_keys = []
            for entry in entries:
                entry_keys.append(entry.key())

            return {"ids": entry_keys}, 200

        

        new_id = db.child("NextID").get(token=idToken).val()
        db.child("NextID").set((new_id + 1), token=idToken)

        args = parser.parse_args()
        db.child("Projects").child(new_id).child("Name").set(args["name"], token=idToken)
        db.child("Projects").child(new_id).child("Description").set(args["description"], token=idToken)
        db.child("Projects").child(new_id).child("Begin Date").set(args["begin_date"], token=idToken)
        db.child("Projects").child(new_id).child("End Date").set(args["end_date"], token=idToken)
        db.child("Projects").child(new_id).child("ID").set(new_id, token=idToken)
        db.child("Projects").child(new_id).child("Issues").set("", token=idToken)
        db.child("Projects").child(new_id).child("Status").set("OPEN", token=idToken)
        db.child("Projects").child(new_id).child("Assignees").set("", token=idToken)

        return {"id": new_id}, 201

class UserList(CredResource):
    """
    A collection of Users.
    """
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("idToken", required=True)
        parser.add_argument("first_name", required=True)
        parser.add_argument("last_name", required=True)
        parser.add_argument("email", required=True)
        parser.add_argument("password", required=True)
        parser.add_argument("type", required=True)

        args = parser.parse_args()
        idToken = args["idToken"]

        if args["first_name"] == "" and args["last_name"] == "" and args["email"] == "" and args["password"] == "" and args["type"] == "":
            # Treat as GET request
            entries = db.child("Users").get(token=idToken).each()
            entry_keys = []
            for entry in entries:
                entry_keys.append(entry.key())

            return {"ids": entry_keys}, 200

        new_id = db.child("NextID").get(token=idToken).val()
        db.child("NextID").set((new_id + 1), token=idToken)

        
        db.child("Users").child(new_id).child("First Name").set(args["first_name"], token=idToken)
        db.child("Users").child(new_id).child("Last Name").set(args["last_name"], token=idToken)
        db.child("Users").child(new_id).child("Email").set(args["email"], token=idToken)
        db.child("Users").child(new_id).child("Password Hash").set(generate_password_hash(args["password"]), token=idToken)
        db.child("Users").child(new_id).child("ID").set(new_id, token=idToken)
        db.child("Users").child(new_id).child("Type").set(args["type"], token=idToken)
        db.child("Users").child(new_id).child("Authorized").set("False", token=idToken)

        firebase.auth().create_user_with_email_and_password(args["email"], args["password"])

        return {"id": new_id}, 201