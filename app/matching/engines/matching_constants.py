TAG_TO_TAG_ENGINE = "tag_to_tag_score"
TAG_TO_INTEREST_ENGINE = "tag_to_interest_score"
SECTOR_TO_SECTOR_ENGINE = "sector_to_sector_score"
ACTIVITY_SCORE_ENGINE = "activity_score"
USER_TO_USER_SCORE_DEVIATION_ENGINE = "user_to_user_score_deviation_score"

ENGINE_WEIGHTAGE_MAP = {
    USER_TO_USER_SCORE_DEVIATION_ENGINE: 0.1,
    TAG_TO_TAG_ENGINE: 0.15,
    TAG_TO_INTEREST_ENGINE: 0.35,
    SECTOR_TO_SECTOR_ENGINE: 0.15,
    ACTIVITY_SCORE_ENGINE: 0.25
}

TOPIC_GROUP_MULTIPLIER = {
    "Building a business": 1.3,
    "Startup Funding": 1.3,
    "Financial planning": 1.1,
    "Career growth": 1.2,
    "Product development": 1.5,
    "Tech (AI/ML)": 1.5,
    "Entrepreneurship": 1.6,
    "Stock market": 1.7
}
