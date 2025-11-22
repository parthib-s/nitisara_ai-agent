from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import datetime

def create_bill_pdf(data):
    os.makedirs("generated_bills", exist_ok=True)
    file_name = f"Bill_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join("generated_bills", file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Laid Bill / Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Company: {data.get('company_name', 'N/A')}")
    c.drawString(50, height - 100, f"Date: {datetime.datetime.now().strftime('%d-%m-%Y')}")

    c.line(50, height - 110, width - 50, height - 110)
    y = height - 140
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Description")
    c.drawString(300, y, "Amount")
    c.setFont("Helvetica", 12)
    y -= 20

    for item in data.get("items", []):
        c.drawString(50, y, item.get("description", ""))
        c.drawString(300, y, f"{item.get('amount', 0)}")
        y -= 20

    c.line(50, y - 10, width - 50, y - 10)
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Tax: {data.get('tax', 0)}%")
    y -= 20
    c.drawString(50, y, f"Total: ₹{data.get('total_amount', 0)}")

    c.save()
    return file_path
