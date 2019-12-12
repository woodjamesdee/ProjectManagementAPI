# ProjectManagementAPI
Intended to be the backend of a management system that functions similarly to Trello or ZenHub. 

## Data Structures

### Issue
Typically a request or intended item of action, an issue is a collection of information able to be categorized.
Issues can be OPEN (in-progress) or CLOSED (complete).

Fields:
* name: A brief title of this Issue. Ex. "Design main character model"
* description: Any and all supporting information for this Issue. Ex. "Must have a red shirt and blue pants"
* id: An auto-assigned value that serves as a unique identifier for this Issue. Ex. 2048
* assignees: Any and all individuals who are assigned to complete this Issue. Ex. "James"
* priority: The importance of this task as described by the Issue creator. Will be a value from 1-10 inclusive. Ex. "10: Mission Critical"
* labels: A collection of brief descriptions commonly used by Issues. Ex. "bug"
* status: The status of this Issue, whether OPEN or CLOSED.

### Project
A collection of Issues which are all related by some common purpose. Could also be referred to as a "Milestone."
Projects can be OPEN (in-progress) or CLOSED (complete).

Fields:
* name: A brief title of this Project. Ex. "Sprint 11"
* description: Any and all supporting information for this Project. Ex. "Completing this user interface for the application"
* id: An auto-assigned value that serves as a unique identifier for this Issue. Ex. 4096
* issues: A collection of all the Issues contained within this Project. Stored in the form of Issue IDs.
* begin_date: The date that work on this Project begins. Ex. 9 January 2020
* end_date: The date that work on this Project is projected to be complete. Ex. 8 January 2021
* status: The status of this Project, whether OPEN or CLOSED.

### User
An individual who may use the API in some capacity. A User has various permissions
depending on the type of User that they are.

Fields:
* first_name: The first name of this User. Ex. "James"
* last_name: The last name of this User. Ex. "Wood"
* email: The email associated with this User. Ex. "test@test.com"
* password_hash: A hashed version of this User's password.
* id: An auto-assigned value that serves as a unique identifier for this User. Ex. 8192
* type: The type of User, which affects permissions. Types include: admin, client, developer.

## Intended Features
Please note some of these features require certain permissions to use.

### Submit Issue ("/issues")
Given a POST request containing the required information in a predefined JSON format, a new Issue can be 
created a stored in the API's backing database.

Values not requested by the predefined format will either be automatically decided by the API or
can be altered after an Issue has already been created.

JSON Data Structure:
{
    "name": <string>,
    "description": <string>,
    "priority": <integer>
}

### View Issue ("/issues/<issue id>")
Given a GET request using the ID of the intended Issue, the information contained within the Issue will be
returned in the following format:

JSON Data Structure:
{
    "name": <string>,
    "description": <string>,
    "id": <integer>,
    "assignees": <string>,
    "priority": <integer>,
    "labels": <string>,
    "status": <string>
}

### View All Issue IDs ("/issues")
Given a GET request at "/issues" the following information will be returned:

JSON Data Structure:
{
    "ids": <array>
}

### Submit Project ("/projects")
Given a POST request containing the required information in a predefined JSON format, a new Project can be 
created a stored in the API's backing database.

Values not requested by the predefined format will either be automatically decided by the API or
can be altered after an Project has already been created.

JSON Data Structure:
{
    "name": <string>,
    "description": <string>,
    "begin_date": <string>,
    "end_date": <string>
}

### View Project ("/projects/<project id>")
Given a GET request using the ID of the intended Project, the information contained within the Issue will be
returned in the following format:

JSON Data Structure:
{
    "name": <string>,
    "description": <string>,
    "id": <integer>,
    "begin_date": <string>,
    "end_date": <string>,
    "status": <string>
}

### View All Project IDs ("/projects")
Given a GET request at "/projects" the following information will be returned:

JSON Data Structure:
{
    "ids": <array>
}