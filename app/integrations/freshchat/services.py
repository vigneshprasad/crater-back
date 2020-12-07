from cryptography.fernet import Fernet

from freelance.settings import FRONT_URL, FERNET_KEY

from utils.tiny_url_service import tiny_url_service

def create_public_url(user, meeting):
    """
    Creating a public url from the user id
    and meeting id and encrypting it using a
    secret key
    """
    message = "" + str(user.uuid) + "|" + str(meeting.id)
    f = Fernet(FERNET_KEY)
    encrypted_message = f.encrypt(message.encode())
    url = 'https://{}/public/rsvp?p={}'.format(FRONT_URL, encrypted_message.decode())
    short_url = tiny_url_service.shorten(url)
    return short_url
