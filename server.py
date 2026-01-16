from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from main import extract_text
from field_extractor import extract_invoice_number, extract_date, extract_total_amount
from fpdf import FPDF
import os

app = FastAPI()

class InvoiceResponse(BaseModel):
    texts: List[str]
    invoice_number: str
    date: str
    total_amount: str

def extract_fields(texts):
    supplier = ""
    supplier_gstin = ""
    bill_to = ""
    ship_to = ""
    products = []

    for i, line in enumerate(texts):
        line_lower = line.lower()
        if "traders" in line_lower or "ltd" in line_lower or "pvt" in line_lower:
            supplier = line.strip()
        elif "gstin" in line_lower and i + 1 < len(texts):
            supplier_gstin = texts[i + 1].strip()
        elif "bill" in line_lower and i + 1 < len(texts):
            bill_to = texts[i + 1].strip()
        elif "ship" in line_lower and i + 1 < len(texts):
            ship_to = texts[i + 1].strip()
        elif any(prod in line for prod in ["SIEMENS","Crompton","HAVELLS","LARSEN","TOUBRO","PVC"]):
            products.append(line.strip())
    return supplier, supplier_gstin, bill_to, ship_to, products

def create_invoice_pdf(ocr_output, filename="digital_invoice.pdf"):
    supplier, gstin, bill_to, ship_to, products = extract_fields(ocr_output["texts"])
    invoice_number = ocr_output.get("invoice_number", "N/A")
    date = ocr_output.get("date", "N/A")
    total_amount = ocr_output.get("total_amount", "0")

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()

    # Header
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "E-INVOICE", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, f"Invoice No.: {invoice_number}", ln=True)
    pdf.cell(0, 6, f"Date: {date}", ln=True)
    pdf.cell(0, 6, f"Supplier: {supplier}", ln=True)
    pdf.cell(0, 6, f"GSTIN: {gstin}", ln=True)
    pdf.ln(5)

    # Bill To / Ship To
    pdf.set_font("Arial", "B", 12)
    pdf.cell(95, 6, "Bill To", border=1)
    pdf.cell(95, 6, "Ship To", border=1, ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(95, 6, bill_to, border=1)
    pdf.cell(95, 6, ship_to, border=1, ln=True)
    pdf.ln(5)

    # Products Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(10, 8, "S.No", border=1, align="C")
    pdf.cell(150, 8, "Product", border=1, align="C")
    pdf.cell(30, 8, "Qty", border=1, align="C")
    pdf.cell(30, 8, "Price", border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", "", 12)
    for idx, prod in enumerate(products, 1):
        pdf.cell(10, 8, str(idx), border=1, align="C")
        pdf.cell(150, 8, prod, border=1)
        pdf.cell(30, 8, "-", border=1, align="C")  # Qty placeholder
        pdf.cell(30, 8, "-", border=1, align="C")  # Price placeholder
        pdf.ln()

    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, f"Total Amount: Rs. {total_amount}", ln=True, align="R")

    # Footer
    pdf.set_font("Arial", "I", 10)
    pdf.set_y(-20)
    pdf.cell(0, 5, "This is a system generated invoice.", align="C")

    pdf.output(filename)
    return filename

@app.post("/extract", response_model=InvoiceResponse)
async def extract_invoice_fields(file: UploadFile = File(...)):
    image_bytes = await file.read()
    texts = extract_text(image_bytes)

    invoice_number = extract_invoice_number(texts)
    date = extract_date(texts)
    total_amount = extract_total_amount(texts)

    ocr_output = {
        "texts": texts,
        "invoice_number": invoice_number,
        "date": date,
        "total_amount": total_amount
    }

    # Generate professional PDF
    create_invoice_pdf(ocr_output)
    

    return InvoiceResponse(
        texts=texts,
        invoice_number=invoice_number,
        date=date,
        total_amount=total_amount
    )

@app.get("/download-invoice")
async def download_invoice():
    pdf_file = "digital_invoice.pdf"
    if os.path.exists(pdf_file):
        return FileResponse(pdf_file, media_type="application/pdf", filename=pdf_file)
    return {"error": "Invoice not found."}
