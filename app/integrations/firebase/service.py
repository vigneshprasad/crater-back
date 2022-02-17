import firebase_admin

from firebase_admin import credentials, auth, firestore

from integrations.firebase.constants import FIREBASE_CONFIG

from freelance import settings

class Firebase():
  app = None
  db = None

  def __init__(self):
    cred = credentials.Certificate(FIREBASE_CONFIG)
    self.app = firebase_admin.initialize_app(cred)
    self.db = firestore.client()
    print("ready")
  
  def register_user(self, user):
    additional_claims = {
      "email": user.email,
      "username": user.username,
    }
    uuid = str(user.pk)
    custom_token = auth.create_custom_token(uuid, additional_claims)
    
    return custom_token
  
  def set_document(self, document_id, collection, data):
    if settings.ENVIRONMENT != settings.ENVIRONMENT_PROD:
        document_id = settings.ENVIRONMENT + "_" + document_id
    ref = self.db.collection(collection).document(document_id)
    print(ref)
    updated = ref.set(data, merge=True)
    print(updated)
    return updated
  
  
firebase = Firebase()