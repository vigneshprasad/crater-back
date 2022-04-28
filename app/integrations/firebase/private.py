from integrations.firebase.service import firebase_service
from integrations.firebase import constants


def get_or_register_admin():
    """Get or register admin in firebase for sending actions in chat."""

    admin_uid = constants.FIREBASE_CHAT_ADMIN_UID

    admin = firebase_service.get_document(
        document_id=admin_uid,
        collection="user_details"
    )

    if admin.exists:
        return admin_uid

    # Register `admin` user on firebase
    firebase_service.custom_registration(
        user_pk=admin_uid,
        email=constants.FIREBASE_CHAT_ADMIN_EMAIL,
        username=constants.FIREBASE_CHAT_ADMIN_USERNAME
    )

    # Add `admin` to user details document
    firebase_service.set_document(
        document_id=admin_uid,
        collection="user_details",
        data={
            "pk": constants.FIREBASE_CHAT_ADMIN_UID,
            "email": constants.FIREBASE_CHAT_ADMIN_EMAIL,
            "name": "Admin",
            "first_name": "Admin"
        }
    )

    return admin_uid
