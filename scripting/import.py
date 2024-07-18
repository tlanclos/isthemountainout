import csv
import sqlite3
from datetime import datetime

filename = 'C:\\Users\\Taylor\\Documents\\sandbox\\isthemountainout\\IsTheMountainOutState - StateV2.csv'


def amend(connection, row, times):
    time = datetime.strptime(row[0], '%Y-%m-%dT%H:%M:%S')
    if time in times:
        return
    times.add(time)
    cursor = connection.cursor()
    cursor.execute("""
            INSERT INTO classifications (
                classification_time,
                classification,
                should_post,
                was_posted
            ) VALUES (?, ?, ?, ?);
        """, (
        time,
        row[1],
        row[2] == 'TRUE',
        row[2] == 'TRUE'
    ))


with open(filename, 'r') as f:
    header = True
    with sqlite3.connect('\\\\172.16.64.218\\appdata\\isthemountainout-config\\tracker.db') as connection:
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
        times = set()
        for row in csv.reader(f):
            if header:
                header = False
                continue

            amend(connection, row, times)

        connection.commit()
