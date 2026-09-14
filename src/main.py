import csv

with open("data/invoices.csv", "r", newline="") as file:
    reader = csv.DictReader(file)

    for invoice in reader:
        print(invoice)

    amount = 3000
    limit = 5000

    if amonut > limit :
        print("FLAGEED: amount exceeds limit")
    else :
        print ("Clean: amount is within limit")