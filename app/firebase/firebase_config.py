import os 

import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()


FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH",
    "firebase-service-account.json"
)


def initialize_firebase():

    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred = credentials.Certificate(
        FIREBASE_CREDENTIALS_PATH
    )

    firebase_app = firebase_admin.initialize_app(
        cred
    )

    print("========================================")
    print("FIREBASE INITIALIZED SUCCESSFULLY")
    print("========================================")

    return firebase_app
