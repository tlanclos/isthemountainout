import sqlite3

import tensorflow as tf
import numpy as np

from astral import LocationInfo
from astral.sun import sun
from dataclasses import dataclass
from PIL import Image
from common.const import PACIFIC_TIMEZONE
from common.image import ImageProvider
from common.storage import LocalFile
from common.frozenmodel import labels, Label
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


@dataclass
class ClassificationRow:
    date: datetime
    classification: Label
    should_post: Optional[bool]
    was_posted: Optional[bool]


class ClassificationTracker:
    notable_transitions = {
        Label.NIGHT: {Label.HIDDEN, Label.MYSTICAL, Label.BEAUTIFUL},
        Label.HIDDEN: {Label.MYSTICAL, Label.BEAUTIFUL},
        Label.MYSTICAL: {Label.BEAUTIFUL},
        Label.BEAUTIFUL: {Label.HIDDEN},
    }

    def amend(self, classification: ClassificationRow):
        pass

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
        pass

    def should_post(self, classification: Label) -> bool:
        last_classification = self._read_last_notable_classification()
        new_classification_is_notable = classification in ClassificationTracker.notable_transitions[
            last_classification]
        will_classification_settle = self._will_classification_settle_with(
            classification)
        if not new_classification_is_notable and not will_classification_settle:
            print(
                f'Classification will not post because {classification} is not notable from {last_classification} and will not settle')
            return False
        elif not new_classification_is_notable:
            print(
                f'Classification will not post because {classification} is not notable from {last_classification}')
            return False
        elif not will_classification_settle:
            print(
                f'Classification will not post because it will not settle with the new classification, {classification}')
            return False
        else:
            print(
                f'Classification will post because {classification} is notable from {last_classification} and will settle with the new classification')
            return True

    def _will_classification_settle_with(self, classification: Label) -> bool:
        history = [c.classification for c in self.read_latest(count=2)]
        will_it_settle = all(c == classification for c in history)
        next_history = [c.value for c in [*history, classification]]
        if will_it_settle:
            print(
                f'Classification chain {" -> ".join(next_history)} has settled')
        else:
            print(
                f'Classification chain {" -> ".join(next_history)} has not settled')
        return will_it_settle

    def _read_last_notable_classification(self) -> Label:
        """
        Find which classification in the classification history is considered "notable".
        That means that the classification happened on the same day and was posted. Classifications
        that happen at night are considered the reset zone so mountain classifications will always
        be posted the next day.
        """
        yesterday = datetime.now(PACIFIC_TIMEZONE).date() - \
            timedelta(days=1)

        # Search back 100 (around 2 days) rows to see when the last posted
        # classification was and take that as the last classification.
        for row in reversed(self.read_latest(count=100)):
            if row.was_posted or row.classification == Label.NIGHT:
                return row.classification
            elif row.date.date() == yesterday:
                print(
                    f'Post not found since yesterday, assuming {Label.NIGHT}')
                return Label.NIGHT

        # If there has been no posts or night found, just assume that there was
        # night at some point
        return Label.NIGHT


class SqliteClassificationTracker(ClassificationTracker):
    _CLASSIFICATIONS_TABLE_NAME = 'classifications'

    connection: sqlite3.Connection
    dbfile: LocalFile

    def __init__(self, *, dbfile: LocalFile) -> None:
        self.dbfile = dbfile
        self.connection = sqlite3.connect(dbfile.filepath)
        self.__create_database()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(dbfile={self.dbfile})'

    def amend(self, classification: ClassificationRow):
        cursor = self.connection.cursor()
        table_name = SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME
        cursor.execute(
            f"INSERT INTO {table_name} (classification_time, classification, should_post, was_posted) VALUES (?, ?, ?, ?);",
            (classification.date, classification.classification.value, classification.should_post, classification.was_posted))
        cursor.fetchall()
        cursor.close()

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
        cursor = self.connection.cursor()
        table_name = SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME
        cursor.execute(
            f"""
            SELECT classification_time, classification, should_post, was_posted
            FROM {table_name}
            ORDER BY classification_time DESC
            LIMIT ?
            """, (count,))

        rows: List[ClassificationRow] = []
        for row in cursor.fetchall():
            rows.append(ClassificationRow(
                date=row[0], classification=row[1], should_posted=row[2], was_posted=row[3]))
        cursor.close()
        return rows

    def __create_database(self):
        if self.__table_exists(table_name=SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME):
            self.__create_classifications_table(
                table_name=SqliteClassificationTracker._CLASSIFICATIONS_TABLE_NAME)

    def __table_exists(self, *, table_name: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        rows = cursor.rowcount > 0
        cursor.close()
        return rows

    def __create_classifications_table(self, *, table_name: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            f"CREATE TABLE {table_name} (classification_time DATETIME, classification TEXT, should_post BOOLEAN, was_posted BOOLEAN);")
        cursor.fetchall()
        cursor.close()


class Classifier:
    seattle = LocationInfo(
        name='Seattle',
        region='Washington',
        timezone='America/Los_Angeles',
        latitude=47.6209673,
        longitude=-122.348993
    )
    model: tf.keras.Model
    image_provider: ImageProvider

    def __init__(self, *, model: tf.keras.Model, image_provider: ImageProvider):
        self.model = model
        self.image_provider = image_provider

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(model={self.model}, image_provider={self.image_provider})'

    def classify(self, *, image: Image.Image):
        img_array = tf.keras.utils.img_to_array(
            image).astype('float32')
        img_array = tf.expand_dims(img_array, 0)
        score = tf.nn.softmax(self.model.predict(img_array))
        return labels()[np.argmax(score, axis=1)[0]]

    def classify_next(self) -> Tuple[ClassificationRow, Image.Image]:
        image, date = self.image_provider.get()

        print(f'Classifying image for date {date}')
        classification = self.classify(image=image)

        if self.__is_night(date) and classification != Label.NIGHT:
            print(
                f'Faulty classification detected, defaulting to {Label.NIGHT}: was {classification}, but is actually night time')
            classification = Label.NIGHT
        elif not self.__is_night(date) and classification == Label.NIGHT:
            print(
                f'Faulty classification detected, defaulting to {Label.HIDDEN}: was {classification}, but is not night time')
            classification = Label.HIDDEN

        return ClassificationRow(
            date=date,
            classification=classification,
            should_post=None,
            was_posted=None), image

    def __is_night(self, timestamp: datetime) -> bool:
        date = timestamp.replace(tzinfo=PACIFIC_TIMEZONE)
        info = sun(Classifier.seattle.observer, date=datetime(
            year=date.year, month=date.month, day=date.day, tzinfo=PACIFIC_TIMEZONE))
        return date < info['dawn'] or date > info['dusk']
