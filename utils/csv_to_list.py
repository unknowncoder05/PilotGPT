import csv


def csv_to_list(scsv):
    return list(csv.DictReader(scsv, delimiter=','))
