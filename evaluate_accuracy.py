import os
import csv
from ocr_engine import extract_text
from field_extractor import extract_fields

# CONFIG
IMAGES_FOLDER = "test_invoices/"
GROUND_TRUTH_CSV = "ground_truth.csv"  # filename, invoice_number, date, total_amount



# Load ground truth


ground_truth = {}
with open(GROUND_TRUTH_CSV, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        ground_truth[row["filename"]] = {
            "invoice_number": row["invoice_number"],
            "date": row["date"],
            "total_amount": row["total_amount"],
        }



# Evaluate invoices

results = []

for filename, truth in ground_truth.items():
    filepath = os.path.join(IMAGES_FOLDER, filename)

    if not os.path.exists(filepath):
        print(f"WARNING: {filename} not found, skipping.")
        continue

    with open(filepath, "rb") as f:
        image_bytes = f.read()

    # OCR
    texts = extract_text(image_bytes)

    # Field extraction
    fields = extract_fields(texts)

    # Compare with ground truth
    result = {
        "filename": filename,
        "invoice_number_correct": fields["invoice_number"] == truth["invoice_number"],
        "date_correct": fields["date"] == truth["date"],
        "total_correct": fields["total_amount"] == truth["total_amount"],
    }

    results.append(result)



# Accuracy calculations


total_invoices = len(results)
fields_per_invoice = 3
total_fields = total_invoices * fields_per_invoice

# Field-level counts
invoice_number_correct = sum(r["invoice_number_correct"] for r in results)
date_correct = sum(r["date_correct"] for r in results)
total_amount_correct = sum(r["total_correct"] for r in results)

# Field-level accuracy
field_level_accuracy = {
    "invoice_number": invoice_number_correct / total_invoices,
    "date": date_correct / total_invoices,
    "total_amount": total_amount_correct / total_invoices,
}

# Overall accuracy (IMPORTANT CHANGE)
total_correct_fields = (
    invoice_number_correct + date_correct + total_amount_correct
)

overall_accuracy = total_correct_fields / total_fields



# Print report


print("====================================")
print("INVOICE EXTRACTION ACCURACY REPORT")
print("Total invoices evaluated:", total_invoices)

print("\nField-level accuracy:")
for field, acc in field_level_accuracy.items():
    print(f"  {field}: {acc * 100:.2f}%")

print(f"\nOverall accuracy (all fields combined): {overall_accuracy * 100:.2f}%")
print("====================================")
