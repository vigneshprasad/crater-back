from cryptography.fernet import Fernet

from freelance.settings import FRONT_URL, FERNET_KEY


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
    return url
