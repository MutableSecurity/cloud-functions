"""Script for generating alerts when tests fails or configuration changes.

The script corresponds to two different Cloud functions:
- Failed Tests
    - Trigger: new tests report introduced in Firebase
    - Check: if the number of failed tests is greater than the user's settings
    - Entry point: failed_tests_alert_generation 
    - Database: mutablesecurity-default-rtdb
    - Path: dash/{userID}/tests_reports/{reportID}
- Configuration Change
    - Trigger: new information report introduced in Firebase
    - Check: if the reported configuration is different from the previous known
    - Database: mutablesecurity-default-rtdb
    - Path: dash/{userID}/information_reports/{reportID}

An environment variable is required, SENDGRID_API_KEY, that needs to be
populated with the API key generated from SendGrid.
"""
import os

import pyrebase
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


FIREBASE_CONFIG = {
    "apiKey": "AIzaSyCuxxjfdyRRU0IkgmuN07bizMzq90KZeV4",
    "authDomain": "mutablesecurity.firebaseapp.com",
    "databaseURL": "https://mutablesecurity-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "mutablesecurity",
    "storageBucket": "mutablesecurity.appspot.com",
    "messagingSenderId": "256666998300",
    "appId": "1:256666998300:web:91e485c2fd01da8ad871d9",
    "measurementId": "G-Q4EYX6MQST",
    "serviceAccount": "/secrets/firebase-adminsdk-secret.json",
}
SENDER_EMAIL = "hello@mutablesecurity.io"
FAILED_TESTS_TEMPLATE_ID = "d-35f61dea0d424d20bf5aa05770c1b4b1"
CONFIGURATION_CHANGE_TEMPLATE_ID = "d-b8f51d985fb84a5da3fe1927c52dcf46"
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]

class Change:
    name: str
    old_value: str
    new_value: str

    def __init__(self, name, old_value: str, new_value: str) -> None:
        self.name = name
        self.old_value = old_value
        self.new_value = new_value

class EmailDetails:
    receiver_email: str
    receiver_name: str
    agent_name: str
    agent_id: str
    solution_name: str
    solution_id: str
    template_id: str
    message: Mail

    def __init__(
        self,
        receiver_email: str,
        receiver_name: str,
        agent_name: str,
        agent_id: str,
        solution_name: str,
        solution_id: str,
        template_id: str
    ) -> None:
        self.receiver_email = receiver_email
        self.receiver_name = receiver_name
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.solution_name = solution_name
        self.solution_id = solution_id

        self.message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=[(self.receiver_email, self.receiver_name)],
        )
        self.message.template_id = template_id
        self.message.dynamic_template_data = {
            "solution_name": self.solution_name,
            "solution_id": self.solution_id,
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
        }

    def set_configuration_changes(self, changes):
        self.message.dynamic_template_data |= {
            "changes": [
                {
                    "name": change.name,
                    "old_value": change.old_value,
                    "new_value": change.new_value
                } for change in changes
            ]
        }

    def send(self) -> None:
        print(f"An email is sent to {self.receiver_email}.")
        try:
            sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
            sendgrid_client.send(self.message)
        except Exception as e:
            print(e.message)


def get_failed_tests_settings(database, user_id):
    return (
        database.child(
            f"/dash/{user_id}/settings/reporting_configuration/failed_tests_trigger"
        )
        .get()
        .val()
    )

def get_last_two_information_reports(database, user_id):
    return (
        database.child(
            f"/dash/{user_id}/information_reports"
        )
        .order_by_child("timestamp")
        .limit_to_first(2)
        .get()
        .val()
    )

def get_user_and_report_id_from_resource_id(resource_id):
    tokens = resource_id.split("/")

    return (tokens[-3], tokens[-1])


def get_configuration_for_solution(solution_id):
    with open(file="solutions.json", mode="r") as solutions:
        solutions_data = json.load(solutions)

    information = solutions_data["solutions"][solution_id]["information"]

    return [
        key for key, value in information.items()
        if "CONFIGURATION" in value["properties"]
    ]

def count_failed_tests_from_report(report):
    count = 0
    for value in report.values():
        if isinstance(value, bool) and not value:
            count += 1

    return count

def get_solution_id_from_report(database, user_id, new_report):
    solution_id = new_report["solution_id"]

    solution = (
        database.child(f"/dash/{user_id}/solutions/{solution_id}").get().val()
    )
    solution_name = solution["solution_id"]

    return solution_name


def create_email_details_from_report(template_id, database, user_id, new_report):
    solution_id = new_report["solution_id"]

    solution = (
        database.child(f"/dash/{user_id}/solutions/{solution_id}").get().val()
    )
    solution_name = solution["solution_id"]
    agent_id = solution["parent_agent"]

    agent = database.child(f"/dash/{user_id}/agents/{agent_id}").get().val()
    agent_name = agent["alias"]

    agent = database.child(f"/dash/{user_id}/settings/account").get().val()
    email = agent["email"]
    full_name = agent["full_name"]

    return EmailDetails(
        email, full_name, agent_name, agent_id,
        solution_name, solution_id, template_id
    )


def failed_tests_alert_generation(event, context):
    user_id, report_id = get_user_and_report_id_from_resource_id(
        context.resource
    )
    new_report = event["delta"]
    print(
        f"A new report, '{report_id}', was introduced for user '{user_id}':"
        f" {new_report}"
    )

    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    database = firebase.database()

    failed_tests_settings = get_failed_tests_settings(database, user_id)
    current_failed_tests = count_failed_tests_from_report(new_report)
    print(
        f"The set count, {failed_tests_settings}, is compared with the one"
        f" from report, {current_failed_tests}."
    )

    if current_failed_tests >= failed_tests_settings:
        email_details = create_email_details_from_report(
            FAILED_TESTS_TEMPLATE_ID, database, user_id, new_report
        )
        email_details.send()

def configuration_change_alert_generation(event, context):
    user_id, report_id = get_user_and_report_id_from_resource_id(
        context.resource
    )
    new_report = event["delta"]
    print(
        f"A new report, '{report_id}', was introduced for user '{user_id}':"
        f" {new_report}"
    )

    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    database = firebase.database()

    reports = get_last_two_information_reports(database, user_id)
    solution_id = get_solution_id_from_report(database, user_id, reports[1])
    configuration_keys = get_configuration_for_solution(solution_id)
    changes = get_changes_from_reports(reports, configuration_keys)

    if len(changes) > 0:
        email_details = create_email_details_from_report(
            CONFIGURATION_CHANGE_TEMPLATE_ID, database, user_id, new_report
        )
        email_details.set_configuration_changes(changes)
        email_details.send()

def get_changes_from_reports(reports, configuration_keys):
    old_report = reports[0]
    new_report = reports[1]

    changes = []
    for key in configuration_keys:
        if old_report[key] != new_report[key]:
            new_change = Change(key, old_report[key], new_report[key])
            changes.append(new_change)

    return changes