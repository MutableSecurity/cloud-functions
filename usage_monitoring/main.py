"""Script for inserting monitoring data into Firebase.

The script connects to a real-time Firebase database and inserts a new document
into the cli_monitoring collection.

To access the Firebase, the scripts needs to have mounted in the above-mentioned
location, /secrets/firebase-adminsdk-secret.json, the secrets of the
administrator account.
"""
import time

import pyrebase
from flask_cors import cross_origin

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


@cross_origin()
def insert_collected_data(request):
    request_json = request.get_json()

    if request_json:
        request_json["timestamp"] = int(time.time())

        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        db = firebase.database()
        db.child("monitoring").push(request_json)

        return f"Succes!"
    else:
        return f"Invalid request!"