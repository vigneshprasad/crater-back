# Run weekly data script for all dates from starting.
from conversations.scripts.get_weekly_data_for_crater import *


def r(start_date, end_date, duration=None, online_count=None):

    # Duration and online count are optional and based on the
    # function we are calculating data for.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Function name here.
        return get_number_of_streams_watched_by_participant(
            start_date=start_date,
            end_date=end_date,
            online_count=online_count
        )


list_of_dates = [
    ("2021-01-01", "2022-01-10"),
    ("2021-01-01", "2022-01-17"),
    ("2021-01-01", "2022-01-24"),
    ("2021-01-01", "2022-01-31"),
    ("2021-01-01", "2022-02-7"),
    ("2021-01-01", "2022-02-14"),
    ("2021-01-01", "2022-02-21"),
    ("2021-01-01", "2022-02-28"),
    ("2021-01-01", "2022-03-07"),
    ("2021-01-01", "2022-03-14"),
    ("2021-01-01", "2022-03-21"),
    ("2021-01-01", "2022-03-28"),
    ("2021-01-01", "2022-04-04"),
    ("2021-01-01", "2022-04-11"),
    ("2021-01-01", "2022-04-18"),
    ("2021-01-01", "2022-04-25"),
    ("2021-01-01", "2022-05-02"),
    ("2021-01-01", "2022-05-09"),
    ("2021-01-01", "2022-05-16"),
    ("2021-01-01", "2022-05-23"),
    ("2021-01-01", "2022-05-30"),
    ("2021-01-01", "2022-06-06"),
    ("2021-01-01", "2022-06-13"),
    ("2021-01-01", "2022-06-20"),
    ("2021-01-01", "2022-06-27"),
    ("2021-01-01", "2022-07-04"),
    # Weekly data.
    ("2022-01-10", "2022-01-17"),
    ("2022-01-17", "2022-01-24"),
    ("2022-01-24", "2022-01-31"),
    ("2022-01-31", "2022-02-7"),
    ("2022-02-07", "2022-02-14"),
    ("2022-02-14", "2022-02-21"),
    ("2022-02-21", "2022-02-28"),
    ("2022-02-28", "2022-03-07"),
    ("2022-03-07", "2022-03-14"),
    ("2022-03-14", "2022-03-21"),
    ("2022-03-21", "2022-03-28"),
    ("2022-03-28", "2022-04-04"),
    ("2022-04-04", "2022-04-11"),
    ("2022-04-11", "2022-04-18"),
    ("2022-04-18", "2022-04-25"),
    ("2022-04-25", "2022-05-02"),
    ("2022-05-02", "2022-05-09"),
    ("2022-05-09", "2022-05-16"),
    ("2022-05-16", "2022-05-23"),
    ("2022-05-23", "2022-05-30"),
    ("2022-05-30", "2022-06-06"),
    ("2022-06-06", "2022-06-13"),
    ("2022-06-13", "2022-06-20"),
    ("2022-06-20", "2022-06-27"),
    ("2022-06-27", "2022-07-04"),
]


def run(duration=False, online_count=False):

    if duration:
        for duration in DATE_JOINED_DURATION_CHOICES:
            print(int(duration/24), "Day")
            for start, end in list_of_dates:
                v = r(start, end, duration=duration)
                print(start, end, v)

    elif online_count:
        for online_count in ONLINE_COUNT_CHOICES:
            print("Online Count: {}".format(online_count))
            for start, end in list_of_dates:
                v = r(start, end, online_count=online_count)
                print(start, end, v)

    else:
        for start, end in list_of_dates:
            v = r(start, end)
            print(start, end, v)
