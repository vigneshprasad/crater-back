PHONE_PRICE_VALIDATION = "phone_price_validation"
INTRODUCTION_VALIDATION = "introduction_validation"
LINKEDIN_URL_VALIDATION = "linkedin_url_validation"
EDUCATION_LEVEL_VALIDATION = "education_level_validation"


VALIDATION_SCORE_HIGH = "Score Too High"
VALIDATION_SCORE_LOW = "Score Too Low"

VALIDATION_SCORE_HIGH_ENUM = 1
VALIDATION_SCORE_LOW_ENUM = 2


LINKEDIN_URL_REGEX = "^((http|https):\/\/)?+(www.linkedin.com\/)+[a-z]+(\/)+[a-zA-Z0-9-]{5,30}+$"

VALID_LINKEDIN_LOCATION_URLS = [
    "www.linkedin.com",
    "linkedin.com",
    "in.linkedin.com",
    "www.linkedin.cn"
]


VALID_SPECIAL_CHARACTERS = [",", " ", "-", ":", "'", ".", "(", ")", "{", "}", "@", "&", "!", "#", "%", "#", "+", "/", "|"]

BLACKLISTED_INTRODUCTION_WORDS = [
    "bhai",
    "love",
    "hey",
    "hi",
    "hello",
    "yes"
]

REGEX_FOR_URL = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
