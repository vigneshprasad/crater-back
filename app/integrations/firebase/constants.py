from django.conf import settings

FIREBASE_CONFIG = {
  "type": "service_account",
  "project_id": "crater-b6a7b",
  "private_key_id": settings.FIREBASE_ACCOUNT_PRIVATE_KEY_ID,
  "private_key": settings.FIREBASE_ACCOUNT_PRIVATE_KEY,
  "client_email": "firebase-adminsdk-xxp09@crater-b6a7b.iam.gserviceaccount.com",
  "client_id": settings.FIREBASE_CLIENT_ID,
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_CERT_URL,
  "client_x509_cert_url": settings.FIREBASE_CLIENT_CERT_URL
}
