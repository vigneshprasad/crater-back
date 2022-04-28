import firebase_admin
import requests

from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import firestore
from django.conf import settings

from integrations.firebase import constants


class FirebaseService:
    """Firebase service."""
    app = None
    db = None

    FIREBASE_API_ENDPOINTS = {
        "send_message": "https://us-central1-crater-b6a7b.cloudfunctions.net/sendMessage"
    }

    def __init__(self, config):
        """Initialise firebase connection with our config."""
        cred = credentials.Certificate(config)
        self.app = firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    @staticmethod
    def get_value_by_env(value):
        """Return value based on environment."""
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            value = settings.ENVIRONMENT + "_" + value

        return value

    def register(self, user):
        """Register user to Firebase DB."""
        additional_claims = {
            "email": user.email,
            "username": user.username,
        }
        uuid = str(self.get_value_by_env(user.pk))
        token = auth.create_custom_token(
          uuid,
          additional_claims
        )
        return token

    def custom_registration(self, email, username, user_pk):
        """Register user to Firebase DB."""
        additional_claims = {
            "email": email,
            "username": username,
        }
        uuid = str(self.get_value_by_env(user_pk))
        token = auth.create_custom_token(
            uuid,
            additional_claims
        )
        return token

    def set_document(self, document_id, collection, data):
        """Set a document on Firebase DB."""
        document_id = str(self.get_value_by_env(document_id))
        ref = self.db.collection(collection).document(document_id)
        updated = ref.set(data, merge=True)
        return updated

    def send_message(self, data, group_id, sender):
        data["group"] = str(self.get_value_by_env(group_id))
        data["sender"] = str(self.get_value_by_env(sender))

        resp = requests.post(
            self.FIREBASE_API_ENDPOINTS["send_message"],
            data
        )

        return resp.text

    def get_document(self, document_id, collection):
        """Get a user by email from document on Firebase DB."""
        document_id = str(self.get_value_by_env(document_id))
        ref = self.db.collection(collection).document(document_id)
        document = ref.get()
        return document


firebase_service = FirebaseService(
    config=constants.FIREBASE_CONFIG
) if settings.FIREBASE_ACCOUNT_PRIVATE_KEY else None
