SLACK_DEFAULT_CHANNEL_ID = "C047DK52PRQ"

# TODO(Nishant): Confirm what template to send to slack in case of failure.
SLACK_ALERT_FOR_OTP_FAILURE = "Hey <!channel>,\n *{failed_otps}* OTPs have been generated " \
                              "since the last successful OTP.\n\n" \
                              "*Last Successful OTP was at: {last_successful_otp_time}*.\n" \
                              "Check admin dashboard to see what's up: " \
                              "<{back_url}/admin/crater_auth/phoneotp/| Phone OTPs>"


SLACK_ALERT_FOR_LOGIN_FAILURE = "Hey <!channel>, \n Some one is trying to login with\n" \
                                "*Phone Number: {phone_number}*\n. But there are {total_users}" \
                                "users with the same phone number on backend.\n" \
                                "Please delete old/unused accounts here: " \
                                "<{back_url}admin/users/user/?q={phone_number}| Users Dashboard>"
