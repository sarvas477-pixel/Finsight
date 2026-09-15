import csv


with open("data/invoices.csv", "r", newline="") as file:
    reader = csv.DictReader(file)

    for invoice in reader:
        print(invoice)