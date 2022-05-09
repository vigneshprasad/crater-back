from conversations.models import *
from users.models import *

# Create category rsvp map
categories = Category.objects.values_list("name", flat=True)

for c in categories:
    print("-----")
    if c != "Coding":
        continue

    user_ids = Request.objects.filter(
        group__categories__name=c,
        group__start__gte="2022-02-01",
    ).values_list("requester", flat=True)
    # users = User.objects.filter(pk__in=user_ids)

    category_rsvped_map = {}
    print(c)

    for user_id in user_ids:
        # print("*****")
        # print(user_id)
        all_rsvps = Request.objects.filter(requester_id=user_id).order_by("created_at")
        # print(all_rsvps.count())
        first_rsvp = all_rsvps.first()
        first_rsvp_categories = first_rsvp.group.categories.values_list("name", flat=True)
        if c not in first_rsvp_categories:
            continue
        # print(c)
        rsvp_categories = all_rsvps.values_list("group__categories__name", flat=True)
        rsvp_categories = list(set(rsvp_categories))
        # print(rsvp_categories)
        for rsvp_category in rsvp_categories:
            if category_rsvped_map.get(rsvp_category):
                category_rsvped_map[rsvp_category] += 1
            else:
                category_rsvped_map[rsvp_category] = 1
        # print("*****")

    print(category_rsvped_map)
    # break
    print("-----")
