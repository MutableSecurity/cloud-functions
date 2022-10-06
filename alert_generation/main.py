"""Script for generating alerts when tests fails.

The script is triggered when a new report is introduced in Firebase. It checks
if the number of failed tests is greater than the user's settings. If it is the
case, then an email is sent.

The trigger is configured as follows:
- Database: mutablesecurity-default-rtdb
- Path: dash/{userID}/tests_reports/{reportID}

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
TEMPLATE_ID = "d-35f61dea0d424d20bf5aa05770c1b4b1"
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]


class EmailDetails:
    receiver_email: str
    receiver_name: str
    agent_name: str
    agent_id: str
    solution_name: str
    solution_id: str
    message: Mail

    def __init__(
        self,
        receiver_email: str,
        receiver_name: str,
        agent_name: str,
        agent_id: str,
        solution_name: str,
        solution_id: str,
    ) -> None:
        self.receiver_email = receiver_email
        self.receiver_name = receiver_name
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.solution_name = solution_name
        self.solution_id = solution_id

        self.__init_sendgrid_mail()

    def __init_sendgrid_mail(self) -> None:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=[(self.receiver_email, self.receiver_name)],
        )

        message.dynamic_template_data = {
            "solution_name": self.solution_name,
            "solution_id": self.solution_id,
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
        }
        message.template_id = TEMPLATE_ID

        self.message = message

    def send(self) -> None:
        print(f"An email is sent to {self.receiver_email}.")
        try:
            sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
            response = sendgrid_client.send(self.message)
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


def get_user_and_report_id_from_resource_id(resource_id):
    tokens = resource_id.split("/")

    return (tokens[-3], tokens[-1])


def count_failed_tests_from_report(report):
    count = 0
    for value in report.values():
        if isinstance(value, bool) and not value:
            count += 1

    return count


def create_email_details_from_report(database, user_id, new_report):
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
        email, full_name, agent_name, agent_id, solution_name, solution_id
    )


def alert_generation(event, context):
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
            database, user_id, new_report
        )
        email_details.send()
