import datetime

from django.utils import timezone

from conversations import models


def run(duration):

    categories = models.Category.objects.all()
    now = timezone.now()

    for category in categories:
        groups = models.Group.objects.filter(
            start__lte=now,
            categories=category,
            type=2
        ).order_by("start")

        if groups.count() < 100:
            continue

        print("Category: {}".format(category.name))
        print("Groups count: {}".format(groups.count()))

        total_hosts = list(set(groups.values_list("host", flat=True)))
        print("Total Hosts: {}".format(len(total_hosts)))

        duration_data = []
        for host in total_hosts:
            if host in duration_data:
                continue

            all_stream_by_host = models.Group.objects.filter(host_id=host, type=2).order_by("start")
            first_stream = all_stream_by_host.first()
            last_stream = all_stream_by_host.last()

            if (first_stream.start + datetime.timedelta(hours=duration)) > last_stream.start:
                continue

            duration_data.append(host)

        print(len(duration_data))


def run_all(duration):

    now = timezone.now()
    groups = models.Group.objects.filter(start__lte=now, type=2).order_by("start")
    print("Groups count: {}".format(groups.count()))

    total_hosts = list(set(groups.values_list("host", flat=True)))
    print("Total Hosts: {}".format(len(total_hosts)))

    duration_data = []
    for host in total_hosts:
        if host in duration_data:
            continue

        all_stream_by_host = models.Group.objects.filter(host_id=host, type=2).order_by("start")
        first_stream = all_stream_by_host.first()
        last_stream = all_stream_by_host.last()

        if (first_stream.start + datetime.timedelta(hours=duration)) > last_stream.start:
            continue

        duration_data.append(host)

    print(len(duration_data))
