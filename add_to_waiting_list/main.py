"""Script for adding an email into the waiting list.

The script connects to a real-time Firebase database and inserts a new object
into the WaitingListEmails collection.

To access the Firebase, the scripts needs to have mounted in the above-mentioned
location, /secrets/firebase-adminsdk-secret.json, the secrets of the
administrator account.
"""
import pyrebase
from flask_cors import cross_origin

import re

EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyCuxxjfdyRRU0IkgmuN07bizMzq90KZeV4",
    "authDomain": "mutablesecurity.firebaseapp.com",
    "databaseURL":
    "https://mutablesecurity-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "mutablesecurity",
    "storageBucket": "mutablesecurity.appspot.com",
    "messagingSenderId": "256666998300",
    "appId": "1:256666998300:web:91e485c2fd01da8ad871d9",
    "measurementId": "G-Q4EYX6MQST",
    "serviceAccount": "/secrets/firebase-adminsdk-secret.json"
}


@cross_origin()
def enter_waiting_list(request):
    # Check if the request is valid
    request_json = request.get_json()
    if request_json and 'email' in request_json:
        email = request_json['email']

        # Check if the email is valid
        if not re.fullmatch(EMAIL_REGEX, email):
            return f'Invalid email!'

        # Connect and get the Firebase database
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        db = firebase.database()

        # Insert data into the database
        data = {'email': email}
        db.child("WaitingListEmails").push(data)

        return f'Succes!'
    else:
        return f'Invalid request!'
