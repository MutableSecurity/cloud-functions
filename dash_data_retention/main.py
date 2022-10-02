"""Script for deleting data older than one month.

The script connects to a real-time Firebase database and deletes data that is older
than one month.

To access the Firebase, the scripts needs to have mounted in
/secrets/firebase-adminsdk-secret.json the secrets of the
administrator account. In addition, the RETENTION_PERIOD_IN_DAYS environment
variable must be set with the number of days in which the data is retained.
"""
import os
import time

import pyrebase

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


def dash_month_retention(event_data, context):
    end_time = get_end_time()

    firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
    database = firebase.database()

    users_ids = get_users_ids(database)
    for user_id in users_ids:
        delete_user_old_data(database, user_id)

    return f"Succes!"

def get_users_ids(database):
    return database.child("dash").shallow().get().val()

def delete_user_old_data(database, uid):
    delete_user_info_reports(database, uid)
    delete_user_tests_reports(database, uid)

def delete_user_info_reports(database, uid):
    delete_all_ond_timestamped_data(database, uid, "information_reports")

def delete_user_tests_reports(database, uid):
    delete_all_ond_timestamped_data(database, uid, "tests_reports")

def delete_all_ond_timestamped_data(database, uid, key):
    end_time = get_end_time()

    firebase_path = f"dash/{uid}/{key}"
    keys_to_remove = database.child(firebase_path).order_by_child("timestamp").end_at(end_time).get().val()
    for key in keys_to_remove.keys():
        key_firebase_path = firebase_path + f"/{key}"
        database.child(key_firebase_path).remove()

def get_end_time():
    retention_period = get_retention_period_in_days()

    return int(time.time()) - retention_period * 24 * 60 * 60

def get_retention_period_in_days():
    return int(os.environ.get("RETENTION_PERIOD_IN_DAYS"))