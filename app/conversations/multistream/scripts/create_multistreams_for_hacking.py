from conversations.multistream import models
from conversations import models as conversation_models


def run(dry_run=True):

    hacking_category = conversation_models.Category.objects.get(name="Hacking")
    streams = conversation_models.Group.objects.filter(
        categories=hacking_category,
        start__date="2022-10-15"
    )

    print("Hacking Streams count: {}".format(streams.count()))
    title_count = 1
    multistream_count = 0

    while multistream_count < streams.count():
        streams_to_add = streams[multistream_count: (multistream_count + 4)]
        multistream_count += 4
        title = "Hacking {}".format(title_count)
        title_count += 1

        print("Multi stream title: {}".format(title))
        print("Steam in multi steam: {}".format(streams_to_add))

        if not dry_run:
            multistream = models.MultiStream.objects.create(
                title=title,
                category=hacking_category
            )
            multistream.streams.add(*streams_to_add)
