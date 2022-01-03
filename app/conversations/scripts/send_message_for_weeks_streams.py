from users import utils as user_utils


WEEKLY_STREAM_MESSAGE = ""


def run(phone_numbers, dry_run=True):

    for phone_number in phone_numbers:
        user_utils.send_sms(
            phone_number=phone_number,
            message=WEEKLY_STREAM_MESSAGE
        )
