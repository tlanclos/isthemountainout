from common.const import mountain_history_filename_template
from common.image import ImageProvider
from common.storage import Storage
from common.time import today


class Snapshotter:
    image_provider: ImageProvider
    store: Storage

    def __init__(self, *, image_provider: ImageProvider, store: Storage) -> None:
        self.image_provider = image_provider
        self.store = store

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(image_provider={self.image_provider}, store={self.store})'

    def snapshot(self):
        today_date = today()
        image, date = self.image_provider.get()

        date_str = date.strftime('%B %d %Y')
        today_str = today_date.strftime('%B %d %Y')

        if date_str != today_str:
            print(
                f'Image date [{date_str}] and today {today_str} do not match, not storing image.')
        else:
            filename = date.strftime(mountain_history_filename_template())
            self.store.save_image(image, filename=filename)
