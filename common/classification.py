import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
from astral import LocationInfo
from astral.sun import sun
from PIL import Image

from common.const import PACIFIC_TIMEZONE
from common.frozenmodel import Label, labels
from common.image import ImageProvider
from common.sqlite import safe_boolean, safe_datetime
from common.storage import LocalFile

try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except:
    from tflite_runtime.interpreter import Interpreter


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

    def read_latest_day(self) -> List[ClassificationRow]:
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

        for row in reversed(self.read_latest_day()):
            if row.should_post or row.was_posted or row.classification == Label.NIGHT:
                return row.classification

            if row.date.date() == yesterday:
                print(
                    f'Post not found since yesterday, assuming {Label.NIGHT}')
                return Label.NIGHT

        # If there has been no posts or night found, just assume that there was
        # night at some point
        return Label.NIGHT


class SqliteClassificationTracker(ClassificationTracker):
    dbfile: LocalFile

    def __init__(self, *, dbfile: LocalFile) -> None:
        self.dbfile = dbfile
        self.__create_database()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(dbfile={self.dbfile})'

    def amend(self, classification: ClassificationRow):
        with self.__connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO classifications (
                    classification_time,
                    classification,
                    should_post,
                    was_posted
                ) VALUES (?, ?, ?, ?);
            """, (
                classification.date,
                classification.classification.value,
                classification.should_post,
                classification.was_posted,
            ))
            connection.commit()

    def read_latest(self, *, count: int) -> List[ClassificationRow]:
        return list(reversed(self.__read("""
            SELECT classification_time, classification, should_post, was_posted
            FROM classifications
            ORDER BY classification_time DESC
            LIMIT ?
        """, (count,))))

    def read_latest_day(self) -> List[ClassificationRow]:
        return self.__read("""
            SELECT classification_time, classification, should_post, was_posted
            FROM classifications
            WHERE classification_time >= (
                SELECT MAX(classification_time)
                FROM classifications
                WHERE classification = 'Night'
            )
            ORDER BY classification_time ASC
        """)

    def __read(self, query: str, parameters: Tuple = ()) -> List[ClassificationRow]:
        with self.__connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            rows: List[ClassificationRow] = []
            column = {
                d[0]: index for index,
                d in enumerate(cursor.description)
            }
            for row in cursor.fetchall():
                rows.append(ClassificationRow(
                    date=safe_datetime(row[column['classification_time']]),
                    classification=Label(row[column['classification']]),
                    should_post=safe_boolean(row[column['should_post']]),
                    was_posted=safe_boolean(row[column['was_posted']])))
            return rows

    def __create_database(self):
        with self.__connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    classification_time DATETIME,
                    classification TEXT,
                    should_post BOOLEAN,
                    was_posted BOOLEAN,
                    PRIMARY KEY(classification_time DESC)
                );
            """)
            connection.commit()

    def __connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.dbfile.filepath)


class Classifier:
    seattle = LocationInfo(
        name='Seattle',
        region='Washington',
        timezone='America/Los_Angeles',
        latitude=47.6209673,
        longitude=-122.348993
    )
    interpreter: Interpreter
    image_provider: ImageProvider

    def __init__(self, *, interpreter: Interpreter, image_provider: ImageProvider):
        self.interpreter = interpreter
        self.image_provider = image_provider

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(interpreter={self.interpreter}, image_provider={self.image_provider})'

    def classify(self, *, image: Image.Image):
        def softmax(logits):
            return np.exp(logits) / np.exp(logits).sum()

        img_array = np.array(image).astype('float32')
        img_array = np.expand_dims(img_array, 0)
        predictor = self.interpreter.get_signature_runner()
        signature = self.interpreter.get_signature_list()
        score = softmax(predictor(
            **{signature['serving_default']['inputs'][0]: img_array})[signature['serving_default']['outputs'][0]])
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
