from src.invoice_pipeline import process_invoice_csv
from src.paths import DEFAULT_INVOICE_CSV


if __name__ == "__main__":
    for result in process_invoice_csv(str(DEFAULT_INVOICE_CSV)):
        print(result)
