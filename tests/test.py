from unittest.mock import patch
import pytest
import sqlite3
import os
import tempfile

from project0.main import (
    extract_incident_data,
    create_database,
    populate_database,
    status,
    get_incident_report,
    main
)

mocked_pdf_content = """
NORMAN POLICE DEPARTMENT
Daily Incident Summary (Public)

8/1/2024 0:04       2024-00055419       1345 W LINDSEY ST       Traffic Stop       OK0140200
8/1/2024 1:15       2024-00055420       789 E MAIN ST       Suspicious Person       OK0140201
"""

extracted_data = [
    ('8/1/2024 0:04', '2024-00055419', '1345 W LINDSEY ST', 'Traffic Stop', 'OK0140200'),
    ('8/1/2025 1:15', '2024-00055420', '789 E MAIN ST', 'Suspicious Person', 'OK0140201')
]

URL = 'https://www.normanok.gov/sites/default/files/documents/2024-08/2024-08-01_daily_incident_summary.pdf'


def copy_pdf_content(url, filename):
    with open(os.path.abspath('tests/mock.pdf'), 'rb') as src:
        with open(filename, 'wb') as dst:
            dst.write(src.read())


@pytest.fixture
def mock_pdf_reader(mocker):
    mock_reader = mocker.Mock()
    mock_page = mocker.Mock()
    mock_page.extract_text.return_value = mocked_pdf_content
    mock_reader.pages = [mock_page]
    return mock_reader


@pytest.fixture
def temp_db():
    db_path = create_database()
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_extract_incident_data(mock_pdf_reader, mocker):
    with patch('project0.main.PdfReader', return_value=mock_pdf_reader):
        temp_dir = os.path.dirname(os.path.abspath(__file__))
        with tempfile.NamedTemporaryFile(dir=temp_dir, delete=True) as temp_pdf:
            temp_pdf.flush()
            result = extract_incident_data(temp_pdf.name)
            assert len(result) == 2
            assert result[0] == ['8/1/2024 0:04', '2024-00055419', '1345 W LINDSEY ST', 'Traffic Stop', 'OK0140200']
            assert result[1] == ['8/1/2024 1:15', '2024-00055420', '789 E MAIN ST', 'Suspicious Person', 'OK0140201']


def test_populate_database(temp_db):
    populate_database(temp_db, extracted_data)
    with sqlite3.connect(temp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        assert count == 2


def test_status(temp_db, capsys):
    populate_database(temp_db, extracted_data)
    status(temp_db)
    captured = capsys.readouterr()
    assert 'Suspicious Person|1\n' in captured.out
    assert 'Traffic Stop|1\n' in captured.out


def test_get_incident_report():
    with patch('urllib.request.urlretrieve') as mock_urlretrieve:
        mock_urlretrieve.side_effect = copy_pdf_content
        data = get_incident_report(URL)
        assert len(data) > 0
        assert data[0] == ['8/1/2024 0:04', '2024-00055419', '1345 W LINDSEY ST', 'Traffic Stop', 'OK0140200']


def test_main_integration(temp_db):
    with patch('urllib.request.urlretrieve') as mock_urlretrieve:
        mock_urlretrieve.side_effect = copy_pdf_content
        main(URL)
        with sqlite3.connect(temp_db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
            assert count == 396
            rows = conn.execute("SELECT * FROM incidents").fetchall()
            assert rows[0] == ('8/1/2024 0:04', '2024-00055419', '1345 W LINDSEY ST', 'Traffic Stop', 'OK0140200')
