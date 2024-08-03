import argparse
import csv
import sqlite3
from datetime import datetime


parser = argparse.ArgumentParser(
    description='Import a CSV file into the database')
parser.add_argument(
    '--file',
    help='Path to the CSV file')
parser.add_argument(
    '--db',
    help='Path to the SQLite DB file')


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


args = parser.parse_args()
with open(args.file, 'r') as f:
    header = True
    with sqlite3.connect(args.db) as connection:
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
