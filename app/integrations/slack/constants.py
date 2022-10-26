SLACK_DEFAULT_CHANNEL_ID = "C047DK52PRQ"


SLACK_ALERT_FOR_OTP_FAILURE = ("Hey <!channel>,\n *{failed_otps}* OTPs have been generated "
                               "since the last successful OTP.\n\n"
                               "*Last Successful OTP was at: {last_successful_otp_time}*.\n"
                               "Check admin dashboard to see what's up:\n\n"
                               "<{back_url}/admin/crater_auth/phoneotp/| Admin Phone OTPs>")


SLACK_ALERT_FOR_LOGIN_FAILURE = ("Hey <!channel>, \n Some one is trying to login with\n"
                                 "*Phone Number: {phone_number}*\n. But there are {total_users}"
                                 "users with the same phone number on backend.\n"
                                 "Please delete old/unused accounts here:\n\n"
                                 "<{back_url}admin/users/user/?q={phone_number}| Admin Users Dashboard>")


SLACK_ALERT_FOR_TWILIO_ACCOUNT_FAILURE = ("Hey <!channel>, \n Twilio account raised a "
                                          "failure error, please check out what it is.\n"
                                          "{error_code} - {error_message}\n\n"
                                          "Check here:\n"
                                          "<twilio.com> | Twilio Dashboard\n"
                                          "<{back_url}/admin/twiliologs/sms/| Admin Twilio SMS Logs>")
