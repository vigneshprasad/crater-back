from urllib.request import urlopen

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from crater.creator import models as creator_models
from crater.rewards import models as reward_models
from crater.sales import constants, models


def run(dry_run=True):
    creators = creator_models.Creator.objects.all()
    default_image_url = "https://1worknetwork-prod.s3.ap-south-1.amazonaws.com/media/listing.png"
    image_temp = NamedTemporaryFile()
    image_temp.write(urlopen(default_image_url).read())
    image_temp.flush()

    for creator in creators:
        reward_type = reward_models.RewardType.objects.filter(
            name="Support"
        ).first()
        if not reward_type:
            continue
        # Check existing reward with Support type if any.
        existing_reward = reward_models.Reward.objects.filter(
            creator=creator,
            type=reward_type
        ).first()

        default_image_url = "https://1worknetwork-prod.s3.ap-south-1.amazonaws.com/media/listing.png"
        image_temp = NamedTemporaryFile()
        image_temp.write(urlopen(default_image_url).read())
        image_temp.flush()

        if existing_reward:
            print("Existing reward with Support type: {}".format(existing_reward.id))
            reward = existing_reward
        else:
            reward = reward_models.Reward(
                creator=creator,
                title="Support my Channel",
                name="Support my Channel",
                description="Helping me upgrade my gear & deliver better content. In return "
                            "you will get better quality content in my subsequent streams.",
                type=reward_type
            )
            reward.photo.save("listing.png", File(image_temp))
            reward.save()

        reward_sale = models.RewardSale(
            reward=reward,
            price=200,
            quantity=100,
            payment_type=constants.SALE_PAYMENT_TYPE_LEARN_ENUM,
            show_in_store=False
        )
        print("Creator: ", creator)
        print("-" * 20)
        reward_sale.save()

    print("End", "-" * 80)
