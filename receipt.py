from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_receipt(player):
    player = dict(player)

    receipt_no = f"MBA-{player['id']:05d}"

    file_path = f"receipts/receipt_{player['id']}.pdf"
    os.makedirs("receipts", exist_ok=True)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # Logo
    c.drawImage("static/logo.png", 50, height - 120, width=80, preserveAspectRatio=True)

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(150, height - 80, "MIRACLE BASKETBALL ACADEMY")

    c.setFont("Helvetica", 11)
    c.drawString(150, height - 100, "Official Payment Receipt")

    # Receipt Info
    y = height - 180
    c.drawString(50, y, f"Receipt No: {receipt_no}")
    c.drawString(50, y-20, f"Date: {datetime.now().strftime('%d %B %Y')}")

    # Player Info
    y -= 60
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Player Information")

    c.setFont("Helvetica", 11)
    y -= 30
    c.drawString(70, y, f"Player Name: {player['full_name']}")
    y -= 20
    c.drawString(70, y, f"Parent Name: {player['parent_name']}")
    y -= 20
    c.drawString(70, y, f"Plan: {player['payment_plan']}")
    y -= 20
    c.drawString(70, y, f"Amount Paid: UGX {player['amount']}")

    # Signature
    y -= 80
    c.drawString(50, y, "Authorized Signature: _____________________")

    c.save()

    return file_path
