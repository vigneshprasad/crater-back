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

    def __init__(self, config):
        """Initialise firebase connection with our config."""
        cred = credentials.Certificate(config)
        self.app = firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    @staticmethod
    def register(user):
        """Register user to Firebase DB."""
        additional_claims = {
            "email": user.email,
            "username": user.username,
        }
        uuid = str(user.pk)
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            uuid = settings.ENVIRONMENT + "_" + uuid
        token = auth.create_custom_token(
          uuid,
          additional_claims
        )
        return token

    @staticmethod
    def custom_registration(email, username, user_pk):
        """Register user to Firebase DB."""
        additional_claims = {
            "email": email,
            "username": username,
        }
        uuid = str(user_pk)
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            uuid = settings.ENVIRONMENT + "_" + uuid
        token = auth.create_custom_token(
            uuid,
            additional_claims
        )
        return token

    def set_document(self, document_id, collection, data):
        """Set a document on Firebase DB."""
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            document_id = settings.ENVIRONMENT + "_" + document_id
        ref = self.db.collection(collection).document(document_id)
        updated = ref.set(data, merge=True)
        return updated

    @staticmethod
    def send_message(data, group_id, sender):
        data["group"] = str(group_id)
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            data["group"] = settings.ENVIRONMENT + "_" + group_id

        uuid = str(sender)
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            uuid = settings.ENVIRONMENT + "_" + uuid

        data["sender"] = uuid

        resp = requests.post(
            "https://us-central1-crater-b6a7b.cloudfunctions.net/sendMessage",
            data
        )

        return resp.text

    def get_document(self, document_id, collection):
        """Get a user by email from document on Firebase DB."""
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            document_id = settings.ENVIRONMENT + "_" + document_id
        ref = self.db.collection(collection).document(document_id)
        document = ref.get()
        return document


firebase_service = FirebaseService(
    config=constants.FIREBASE_CONFIG
) if settings.FIREBASE_ACCOUNT_PRIVATE_KEY else None
