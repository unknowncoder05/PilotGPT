from io import StringIO
import csv

def get_all_keys(list_of_dicts):
    all_keys = []
    for d in list_of_dicts:
        for key in d.keys():
            if key not in all_keys:
                all_keys.append(key)
    return all_keys

def dict_to_csv(data, headers=None, verbose_headers=None, delimiter=';'):
    # Get headers from the specified headers, or use the keys of the first dictionary in the list if headers is not specified
    if headers is None:
        headers = get_all_keys(data)

    # Create a StringIO object for writing the CSV
    csv_buffer = StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=headers if not verbose_headers else headers, delimiter=delimiter)

    # Write the headers and the data to the buffer
    writer.writeheader()
    for row in data:
        row_data = {header: row.get(header, '') for header in headers}
        writer.writerow(row_data)

    # Get the contents of the buffer and return it as a string
    csv_str = csv_buffer.getvalue()
    return csv_str
    