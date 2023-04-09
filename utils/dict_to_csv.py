from io import StringIO
import csv

def dict_to_csv(data, headers=None, delimiter=';'):
    # Get headers from the specified headers, or use the keys of the first dictionary in the list if headers is not specified
    headers = headers if headers is not None else list(
        data[0].keys()) if data else []

    # Create a StringIO object for writing the CSV
    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=headers, delimiter=delimiter)

    # Write the headers and the data to the buffer
    writer.writeheader()
    for row in data:
        row_data = {header: row.get(header, '') for header in headers}
        writer.writerow(row_data)

    # Get the contents of the buffer and return it as a string
    csv_str = csv_buffer.getvalue()
    return csv_str
    