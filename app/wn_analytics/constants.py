USER_CREATED = "signup_user"
AGREEMENT_FILLED = "accept_agreement"
OBJECTIVES_ADDED = "objectives_added"
EMAIL_VERIFIED = "signup_email_verified"
BASIC_PROFILE_CREATED = "signup_basic_profile"
SERVICES_CREATION = "signup_services_user"
PHONE_NUMBER_VERIFIED = "signup_phone_verified"
POST_CREATED = "post_created"
REFERRED_FRIEND = "refer_friend"
REGISTERED_MEETING_PREFERENCES = "register_meeting_preferences"
EDIT_MEETING_PREFERENCES = "edit_meeting_preferences"
MEETING_CONFIG_CREATED = "meeting_config_created"
MEETING_CREATED = "matched_for_meeting"
CREATIVE_EXCHANGE_REQUEST_CREATED = "creative_exchange_request_created"
RSVP_UPDATED = "rsvp_updated"
RESCHEDULE_CREATED = "reschedule_created"
RESCHEDULE_UPDATED = "reschedule_updated"
CONVERSATION_CREATED = "conversation_created"
CONVERSATION_JOINED = "conversation_joined"

# Constants for device population.
SEGMENT_IDENTIFY = "identify"
DEVICE_TYPE_IOS = "ios"

DEFAULT_IOS_DEVICE_MANUFACTURER = "apple"
DEFAULT_IOS_DEVICE_MODEL = "iphone10,1"

FRONT_END_IDENTIFY_CALL_IOS = {
    "anonymousId": "FD419365-2623-470C-B445-36C419892A98",
    "channel": "server",
    "context": {
        "app": {
            "build": "26",
            "name": "",
            "namespace": "com.wurknet.mobile",
            "version": "1.9.2"
        },
        "device": {
            "token": "896e8bb5ee2f3ffc9d7c0e63077bbc79efbd45e6af5fb0942583046c2ff374fc",
            "type": "ios"
        },
        "ip": "223.184.21.146",
        "library": {
            "name": "analytics-ios",
            "version": "3.7.0"
        },
        "locale": "en-IN",
        "network": {
            "carrier": "AirTel",
            "cellular": False,
            "wifi": True
        },
        "os": {
            "name": "iOS",
            "version": "14.6"
        },
        "screen": {
            "height": 812,
            "width": 375
        },
        "timezone": "Asia/Kolkata",
        "traits": {
            "email": "nishantkparashar@gmail.com",
            "email_verified": True,
            "has_introduction": True,
            "intent": "network",
            "is_approved": True,
            "linkedin_url": "https://www.linkedin.com/in/nishant-k-parashar",
            "objectives": [],
            "phone_number": "+918722438458",
            "phone_number_verified": True,
            "role": "user",
            "user_tags": ["Startup Founder"]
        }
    },
    "integrations": {},
    "messageId": "3563AC50-D33C-45CD-990A-AEC8004AF1AA",
    "originalTimestamp": "2021-06-16T11:10:17.974Z",
    "projectId": "uPE38upe1KABCRw7kk6UK2",
    "receivedAt": "2021-06-16T11:10:48.395Z",
    "sentAt": "2021-06-16T11:10:47.458Z",
    "timestamp": "2021-06-16T11:10:18.911Z",
    "traits": {
        "has_introduction": True,
        "role": "user",
        "user_tags": ["Startup Founder"]
    },
    "type": "identify",
    "userId": "e22679b0-03fc-4398-a2f9-45e81813c623",
    "version": 2,
    "writeKey": "iGbaBkLh7gb9l1rkZjGFSqmzkj13z4YN"
}

# Keeping this for testing purposes.
FRONT_END_IDENTIFY_CALL_ANDROID = {
    "anonymousId": "f3691a5b-a7f5-4e94-ad20-13ed740f6397",
    "channel": "server",
    "context": {
        "app": {
            "build": "26",
            "name": "WorkNetwork", "namespace": "com.wurknet.mobile", "version": "1.9.2"
        },
        "device": {
            "id": "8a38de8db925f2be", "manufacturer": "motorola", "model": "moto g(30)", "name": "caprip",
            "token": "fjoaN_jRQOCgfS6wCVsEST:APA91bHVk2kviBWoQgBByrK9eYc3aavHgrqFiz00sDsgQl-LoNTp9bAJ9ZmDoadM1B1rWhow58otJA9GxcCNUvkdEjUbvCsLW5vSEgfk-nMXdUbBmQkb6xgikkc7SBdAyqUi7o0Ryqd9",
            "type": "android"
        },
        "ip": "49.207.195.197",
        "library": {
            "name": "analytics-android",
            "version": "4.7.0"
        },
        "locale": "en-US",
        "network": {
            "bluetooth": False,
            "carrier": "airtel",
            "cellular": False,
            "wifi": True
        },
        "os": {
            "name": "Android",
            "version": "11"
        },
        "screen": {
            "density": 1.75,
            "height": 1473,
            "width": 720
        },
        "timezone": "Asia/Kolkata",
        "traits": {
            "anonymousId": "f3691a5b-a7f5-4e94-ad20-13ed740f6397",
            "email": "vig9295@gmail.com",
            "email_verified": True,
            "intent": "network",
            "is_approved": False,
            "objectives": [],
            "phone_number_verified": False,
            "userId": "0fd379d3-9348-481c-92e0-7b780d4ecbcb"
        },
        "userAgent": "Dalvik/2.1.0 (Linux; U; Android 11; moto g(30) Build/RRCS31.Q1-3-34-1-4)"
    },
    "integrations": {},
    "messageId": "94fd3e11-76e6-4583-9e39-7ca3dd8802c9",
    "originalTimestamp": "2021-06-15T07:57:47.932Z",
    "projectId": "uPE38upe1KABCRw7kk6UK2",
    "receivedAt": "2021-06-15T07:58:11.383Z",
    "sentAt": "2021-06-15T07:58:11.343Z",
    "timestamp": "2021-06-15T07:57:47.972Z",
    "traits": {
        "anonymousId": "f3691a5b-a7f5-4e94-ad20-13ed740f6397",
        "email": "vig9295@gmail.com",
        "email_verified": True,
        "intent": "network",
        "is_approved": False,
        "objectives": [],
        "phone_number_verified": False,
        "userId": "0fd379d3-9348-481c-92e0-7b780d4ecbcb"
    },
    "type": "identify",
    "userId": "0fd379d3-9348-481c-92e0-7b780d4ecbcb",
    "version": 2,
    "writeKey": "iGbaBkLh7gb9l1rkZjGFSqmzkj13z4YN"
}
