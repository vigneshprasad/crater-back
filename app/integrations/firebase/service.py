import firebase_admin

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

    def set_document(self, document_id, collection, data):
        """Set a document on Firebase DB."""
        if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
            document_id = settings.ENVIRONMENT + "_" + document_id
        ref = self.db.collection(collection).document(document_id)
        updated = ref.set(data, merge=True)
        return updated


firebase_service = FirebaseService(
    config=constants.FIREBASE_CONFIG
)
