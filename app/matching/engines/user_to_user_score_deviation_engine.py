def get_score_deviation_score_between_users(user_score, matched_user_score):

    score_deviation_score = 0

    score_deviation = abs(user_score - matched_user_score) / ((user_score + matched_user_score) / 2) * 100

    if score_deviation <= 10:
        score_deviation_score = 100
    elif score_deviation <= 20:
        score_deviation_score = 70
    elif score_deviation <= 30:
        score_deviation_score = 50
    elif score_deviation <= 50:
        score_deviation_score = 20
    elif score_deviation <= 60:
        score_deviation_score = 10

    return score_deviation_score

