import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_receipt_email(to_email: str, order_reference: str, total: float, items: list):
    try:
        items_html = "".join([f"<li>{item['name']} - {item['qty']} x {item['price']}</li>" for item in items])

        params: resend.Emails.SendParams = {
            "from": "onboarding@resend.dev",  # Needs a verified domain
            "to": [to_email],
            "subject": f"Your X-UK Phones Receipt - {order_reference}",
            "html": f"<h1>Thank you for your purchase!</h1><p>Order Reference: {order_reference}</p><p>Total: {total}</p><ul>{items_html}</ul>",
        }
        resend.Emails.send(params)
    except Exception as e:
        print(f"Failed to send email: {e}")
