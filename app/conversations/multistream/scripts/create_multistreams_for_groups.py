from conversations import models as conversation_models
from conversations.multistream import models


# def run(group_ids, dry_run=False):
#     total_groups = len(group_ids)
#     all_groups = conversation_models.Group.objects.filter(id__in=group_ids)
#     i = 0
#
#     while i < (total_groups - 1):
#         j = i + 4
#         groups = all_groups[i: i + 4]
#         topic_int = j / 4
#         topic = "Design {}".format(topic_int)
#
#         print("Creating Multistream")
#         print(topic)
#         print(groups)
#         print(len(groups))
#
#         if not dry_run:
#             multistream = models.MultiStream.objects.create(
#                 topic=topic
#             )
#             multistream.add(*groups)
#
#         i = j


def run(list_of_groups_ids, dry_run=True):

    category = conversation_models.Category.objects.get(name="Design")
    print("Category for all multistreams: {}".format(category))
    print("\n")
    i = 1

    for group_ids in list_of_groups_ids:
        groups = conversation_models.Group.objects.filter(id__in=group_ids)
        topic = "Design November {}".format(i)

        print("Creating multistream with data:\n")
        print("Topic: ", topic)
        print("Streams: ", group_ids)

        i += 1

        if not dry_run:
            multistream = models.MultiStream.objects.create(
                title=topic,
                category=category
            )
            multistream.streams.add(*groups)

            print("Created multistream")
            print("Multistream ID: ", multistream.id)
            # print(multistream.streams.values_list("id", flat=True))

        print("-"*10)
