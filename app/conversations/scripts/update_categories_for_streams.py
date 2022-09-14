import csv
from urllib import request as urllib_request

from conversations import models


def run(
        file_url="https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/update_streams_categories.csv",
        dry_run=True
):

    response = urllib_request.urlopen(file_url)
    lines = [line.decode("utf-8") for line in response.readlines()]
    reader = csv.DictReader(lines)
    # all_groups = [g.__str__() for g in models.Group.objects.filter(
    #     type=2,
    #     categories__name__in=["Design", "Other", "Web 3.0"]
    # )]

    for row in reader:
        print("-----")
        group_id = int(row.get("ID", "").strip())
        if not group_id:
            print("No group with id: {}".format(group_id))
            continue

        topic = row.get("Topic", "").strip()
        group_topic_str = str(group_id) + " - " + topic
        print(group_topic_str)
        # group_str = None
        # for group in all_groups:
        #     if topic in group:
        #         group_str = group
        #         index = all_groups.index(group)
        #         all_groups.pop(index)
        #         break
        #
        # if not group_str:
        #     print("No group str found: {}".format(topic))
        #     continue

        # group_id_from_topic = group_str.split("-")[0]
        # g_id = int(group_id_from_topic.strip())

        # print(g_id, group_id, topic)

        category_list = []
        c1 = row.get("1", "").strip()
        if c1:
            category_list.append(c1)
        c2 = row.get("2", "").strip()
        if c2:
            category_list.append(c2)
        c3 = row.get("3", "").strip()
        if c3:
            category_list.append(c3)
        c4 = row.get("4", "").strip()
        if c4:
            category_list.append(c4)

        group = models.Group.objects.get(id=group_id)
        group_str = group.__str__().replace(" - 2", "")
        if group_topic_str != group_str:
            print("*"*30)

        print(group_str)
        print("Old categories")
        print(group.categories.all())
        print("New categories")
        # print(category_list)
        categories = models.Category.objects.filter(name__in=category_list)
        print(categories)
        if not categories:
            continue

        if not dry_run:
            print("Removed old categories")
            group.categories.clear()
            group.categories.add(*categories)
            print("Updated group with new categories")
            print(group.categories.all())
