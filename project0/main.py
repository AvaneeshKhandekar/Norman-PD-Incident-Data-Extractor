import argparse
import os
import re
import sqlite3
import sys
import tempfile
import urllib.request
from pypdf import PdfReader


def is_header_line(line):
    header_keywords = {
        "NORMAN POLICE DEPARTMENT",
        "Daily Incident Summary (Public)",
        "Location",
        "Date/ Time",
        "Nature",
        "Incident ORI"
    }
    return any(keyword in line for keyword in header_keywords)


def extract_incident_data(file_path):
    pdf_reader = PdfReader(file_path)
    extracted_data = []
    for page in pdf_reader.pages:
        text = page.extract_text(extraction_mode="layout")
        if text is None:
            continue
        for line in text.split("\n"):
            if is_header_line(line):
                continue

            attributes = re.split(r"[ \t\r\n]{5,}", line.strip())

            n = len(attributes)
            if n == 5:
                extracted_data.append(attributes)
            elif n < 5:
                if extracted_data:
                    extracted_data[-1][2] += ' '.join(attributes)
            else:
                continue
    return extracted_data


def create_database():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'normanpd.db'))

    if os.path.exists(db_path):
        os.remove(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute('''
            CREATE TABLE incidents(
                date_time TEXT,
                incident_number TEXT PRIMARY KEY,
                location TEXT,
                nature TEXT,
                incident_ori TEXT
            )
        ''')

    return db_path


def populate_database(db, data):
    with sqlite3.connect(db) as conn:
        conn.executemany('''
            INSERT INTO incidents (date_time, incident_number, location, nature, incident_ori)
            VALUES (?, ?, ?, ?, ?)
        ''', data)
        conn.commit()


def status(db):
    with sqlite3.connect(db) as conn:
        for nature, count in conn.execute('''
            SELECT nature, COUNT(*) as count
            FROM incidents
            GROUP BY nature
            ORDER BY nature
        '''):
            print(f"{nature}|{count}")


def get_incident_report(url):
    file_name = os.path.basename(url)
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, file_name)
        urllib.request.urlretrieve(url, file_path)
        data = extract_incident_data(file_path)
        return data


def main(url):
    data = get_incident_report(url)
    db = create_database()
    populate_database(db, data)
    status(db)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch pdf from API.")
    parser.add_argument("--incidents", type=str, required=True, help="URL of incident report to fetch.")
    args = parser.parse_args()
    if not args.incidents:
        print("Must provide URL of incident report file.")
        sys.exit(1)
    if args.incidents:
        main(args.incidents)
