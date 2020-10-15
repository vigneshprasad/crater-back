import csv
import datetime
from urllib import request as urllib_request

from resources.meetings import services, choices


FIELDS = [
    'Week Start (%d/%m%/%y)',
    'Week End (%d/%m%/%y)',
]


def run(
        file_url='https://1worknetwork-dev.s3.ap-south-1.amazonaws.com/data/meeting_config_data.csv',
        dry_run=True
):
    response = urllib_request.urlopen(file_url)
    lines = [line.decode('utf-8') for line in response.readlines()]
    reader = csv.DictReader(lines)

    for row in reader:
        print('Start', '-' * 80)
        row = dict(row)
        week_start_date = row.get('Week Start').strip()
        week_end_date = row.get('Week End').strip()

        # Meeting Config Population
        week_start_date = datetime.datetime.strptime(week_start_date, '%d/%m/%y')
        week_start_date = week_start_date.date()
        week_end_date = datetime.datetime.strptime(week_end_date, '%d/%m/%y')
        week_end_date = week_end_date.date()

        # Registration starts a few days early.
        registration_start_date = week_start_date - datetime.timedelta(
            days=choices.DEFAULT_REGISTRATION_START_AND_WEEK_START_DELTA
        )
        registration_end_date = week_start_date - datetime.timedelta(
            days=choices.DEFAULT_REGISTRATION_CLOSED_WEEKDAY
        )

        print("Week Start Date: {}".format(week_start_date))
        print("Week End Date: {}".format(week_end_date))
        print("Registration Start Date: {}".format(registration_start_date))
        print("Registration End Date: {}".format(registration_end_date))

        print('End', '-' * 80)

        if not dry_run:
            config = services.create_meeting_config_for_time_period(
                week_start_date,
                week_end_date,
                registration_start_date=registration_start_date,
                registration_end_date=registration_end_date
            )

            config.is_active = False
            config.is_registration_open = False
            config.save()



