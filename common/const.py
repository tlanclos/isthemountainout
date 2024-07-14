import pytz

PACIFIC_TIMEZONE = pytz.timezone('US/Pacific')


def mountain_history_filename_template() -> str:
    return 'MountRainier-%Y-%m-%dT%H_%M_%S'
