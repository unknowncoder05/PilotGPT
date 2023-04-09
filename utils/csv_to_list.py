import csv


def csv_to_list(scsv, headers=None):
    # TODO: use headers
    return list(csv.DictReader(scsv, delimiter=','))
