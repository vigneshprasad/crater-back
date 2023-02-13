from tokens import models


def run():
    user_tokens = models.UserToken.objects.all().order_by("-amount")
    for user_token in user_tokens:
        print(user_token.user.email, "#", user_token.user.display_name, "#", user_token.amount)
