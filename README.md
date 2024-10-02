# Norman PD Incident Data Extraction from PDF

### AUTHOR

##### Avaneesh Khandekar

### INSTALLATION

To Install required dependencies:

``` bash
pipenv install
```

### USAGE

To fetch incident data from a specified PDF report URL:

```bash
pipenv run python project0/main.py --incidents <url>
```

### OVERVIEW

This script extracts incident data from a PDF report generated by the Norman Police Department. It parses the PDF to
extract the following fields for each incident:

- Date/Time: The date and time of the incident.
- Incident Number: A unique identifier for the incident.
- Location: The address where the incident occurred.
- Nature: The type of incident (e.g., Traffic Stop).
- Incident ORI: The Originating Agency Identifier.

Logic to extract the data:

- Make an API call to the url of the hosted PDF and save in a temp file for processing.
- Extract the data using PyPDF library with the following logic:
    - Start reading PDF in layout mode (This preserves the spaces in original pdf).
    - Skip blank lines.
    - Split all text line by line.
    - Iterate over lines:
        - Check if it is a header or default line and continue.
        - Split the lines based on large whitespace. If the space is more than 5 spaces then consider it as one column.
          This is a better approach than visitor function as it is easy to change and manager in case PDF structure
          changes.
        - Reference: https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md (Whitespace characters: How
          many new lines should be extracted for 3cm of vertical whitespace? How many spaces should be extracted if
          there is 3cm of horizontal whitespace? When would you extract tabs and when spaces?)
        - Check record length and add it as a list to result array.
        - If the record length is less than 5 then this is continuation of the location part on the next line. In this
          case update location part of the last added list in the result array.
    - Return Array of extracted of rows to be inserted in table.
- Create database or replace existing database 'normanpd.db' in resources and create table Incidents with following
  schema:
    - Incidents(date_time TEXT, incident_number TEXT PRIMARY KEY, location TEXT, nature TEXT, incident_ori TEXT)
- Populate Database using data from the tuple created before.
- Print nature and its count in STDOUT.

The extracted data is stored in an SQLite database.
The program then executes a SQL query to print all the natures of incidents and how many times each one has occurred in
the following format:\
`{nature}|{count}`

### FUNCTIONS

#### `extract_incident_data(file_path)`

- **Description**: Extracts incident data from a specified PDF file.
- **Params**:
    - `file_path` (string): Path to the PDF file.
- **Returns**: List of lists containing incident data per row.

#### `create_database()`

- **Description**: Creates a new SQLite database and a table for storing incident data.
- **Params**:
    - None
- **Returns**: Path to the created database.

#### `populate_database(db, data)`

- **Description**: Inserts extracted incident data into the SQLite database.
- **Params**:
    - `db` (string): Path to the SQLite database.
    - `data` (list): List of tuples containing incident data.
- **Returns**: None.

#### `status(data)`

- **Description**: Prints the count of incidents grouped by nature.
- **Params**:
    - `db` (string): Path to the SQLite database.
- **Returns**: None, prints to STD OUT.

#### `get_incident_report(url)`

- **Description**: Downloads the incident report from a given URL, stores in a temp file and calls the extract function.
- **Params**:
    - `url` (string): URL of the incident report PDF.
- **Returns**: Extracted incident data.

#### `main(url)`

- **Description**: Main entry point of the script. Fetches data from the incident report URL, creates the database, and
  populates it with incident data.
- **Params**:
    - `url` (string): URL of the incident report PDF.
- **Returns**: None. Just calls all the functions.

### TESTS

#### `test_extract_incident_data`

- **Function Tested**: `extract_incident_data(file_path)`
- **Description**: Tests extraction of incident data from a PDF file.
- **Asserts**: Correctness of extracted incident data.

#### `test_populate_database`

- **Function Tested**: `populate_database(db, data)`
- **Description**: Tests the insertion of incident data into the database.
- **Asserts**: Correctness of the number of records in the database.

#### `test_status`

- **Function Tested**: `status(db)`
- **Description**: Tests status reporting of incidents from the database.
- **Asserts**: Correctness of printed status information.

#### `test_get_incident_report`

- **Function Tested**: `get_incident_report(url)`
- **Description**: Tests the retrieval and extraction of incident data from a PDF report URL.
- **Asserts**: Validates that the data is extracted correctly.

#### `test_main_integration`

- **Function Tested**: `main(url)`
- **Description**: Tests the full integration from fetching the PDF to inserting data into the database.
- **Asserts**: Ensures that data is correctly inserted into the database.

### ASSUMPTIONS:

- **URL**: It is assumed that the URL is correct and PDF file exists.
- **Valid Data Format**: It is assumed that columns will be separated by more than 5 white spaces.
- **Multi Line**: It is assumed that only location part will run into next line and other elements will be part of
  current line.