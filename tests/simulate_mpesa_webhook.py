"""Simulate a Safaricom M-Pesa STK callback against the local server.

Why this exists
---------------
Real M-Pesa callbacks only happen on Safaricom's network, and you cannot trigger
them on demand. This script lets you fake one locally so you can test the
"payment succeeded / cancelled / failed" paths and watch stock get released.

Usage
-----
  1. Start the server:  uvicorn app.main:app --reload
  2. Find a pending order:  GET /admin/orders   (copy its checkout_request_id)
  3. Run:
       python tests/simulate_mpesa_webhook.py <checkout_request_id>
       python tests/simulate_mpesa_webhook.py <checkout_request_id> LMP1234567       # success
       python tests/simulate_mpesa_webhook.py <checkout_request_id> - --cancel       # user cancelled
"""

import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"
CALLBACK_URL = f"{BASE_URL}/payments/callback"  # canonical webhook


def simulate_mpesa_callback(checkout_request_id: str, receipt_no: str = "LMP1234567", success: bool = True):
    if success:
        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 65000},
                            {"Name": "MpesaReceiptNumber", "Value": receipt_no},
                            {"Name": "TransactionDate", "Value": 20260101120000},
                            {"Name": "PhoneNumber", "Value": 254700000000},
                        ]
                    },
                }
            }
        }
    else:
        # 1032 = cancelled by user; anything else = payment failed
        payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user",
                }
            }
        }

    response = httpx.post(CALLBACK_URL, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tests/simulate_mpesa_webhook.py <checkout_request_id> [receipt] [--cancel]")
        sys.exit(1)

    checkout_id = sys.argv[1]
    cancel = "--cancel" in sys.argv
    receipt = "LMP1234567"
    for arg in sys.argv[2:]:
        if not arg.startswith("--") and arg != "-":
            receipt = arg

    simulate_mpesa_callback(checkout_id, receipt, success=not cancel)
