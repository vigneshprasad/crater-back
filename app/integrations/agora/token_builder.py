import time

from integrations.agora import _access_token
from integrations.agora import constants


class RtcTokenBuilder:

    def __init__(self, privilege_expiry_ts=None):
        self.app_id = constants.APP_ID
        self.app_certificate = constants.APP_CERTIFICATE
        self.privilege_expiry_ts = self._get_privilege_expiry_ts(privilege_expiry_ts)

    @staticmethod
    def _get_privilege_expiry_ts(privilege_expiry_ts=None):
        """Generates privilege expiry ts for token if not provided.

        Args:
            privilege_expiry_ts: represented by the number of seconds elapsed since
                1/1/1970. If, for example, you want to access the
                Agora Service within 10 minutes after the token is
                generated, set expireTimestamp as the current.

        """
        if privilege_expiry_ts:
            return privilege_expiry_ts

        expiry_time_in_seconds = constants.DEFAULT_EXPIRY_TIME
        current_ts = int(time.time())
        return current_ts + expiry_time_in_seconds

    def build_token_with_uid(self, channel_name, uid, role):
        """Build token using account for Agora connection.

        Args:
            channel_name: Unique channel name for the AgoraRTC session in the string format
            uid: User ID. A 32-bit unsigned integer with a value ranging from
                1 to (2^32-1). optionalUid must be unique.
            role: role_publisher = 1: A broadcaster (host) in a live-broadcast profile.
                role_subscriber = 2: (Default) A audience in a live-broadcast profile.

        """

        return self.build_token_with_account(
            channel_name,
            uid,
            role,
        )

    def build_token_with_account(self, channel_name, account, role):
        """Build token using account for Agora connection.

        Args:
            channel_name:Unique channel name for the AgoraRTC session in the string format
            account: The user account.
            role: role_publisher = 1: A broadcaster (host) in a live-broadcast profile.
                role_subscriber = 2: (Default) A audience in a live-broadcast profile.

        """

        token = _access_token.AccessToken(self.app_id, self.app_certificate, channel_name, account)
        token.addPrivilege(_access_token.kJoinChannel, self.privilege_expiry_ts)

        if role in [constants.ROLE_ATTENDEE, constants.ROLE_ADMIN, constants.ROLE_PUBLISHER]:
            token.addPrivilege(_access_token.kPublishVideoStream, self.privilege_expiry_ts)
            token.addPrivilege(_access_token.kPublishAudioStream, self.privilege_expiry_ts)
            token.addPrivilege(_access_token.kPublishDataStream, self.privilege_expiry_ts)

        return token.build()
