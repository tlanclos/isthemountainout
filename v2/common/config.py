def mountain_history_bucket_name() -> str:
    return 'mountain-history'


def mountain_history_filename_template() -> str:
    return 'MountRainier-%Y-%m-%dT%H:%M:%S'


def classification_bucket_name() -> str:
    return 'isthemountainout.appspot.com'


def classification_filename() -> str:
    return 'mountain-history.classifications.json'


def brand_filename() -> str:
    return 'branding_1920x1080.png'


def model_bucket_name() -> str:
    return 'isthemountainout.appspot.com'


def model_filename() -> str:
    return 'v2/isthemountainout.h5'
