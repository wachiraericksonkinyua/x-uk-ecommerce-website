"""M-Pesa reconciliation must be shared by the webhook and the tracking poll.

Regression: a successful payment whose callback carries the ResultCode as the
string "0" (or a malformed payload) was being marked "Payment Failed".
"""

import app.services.inventory as inventory
import app.services.mpesa as mpesa
from tests.fakes import FakeSupabase


def _store(status="Pending PIN"):
    fake = FakeSupabase()
    fake.store["orders"] = [
        {
            "id": "o1",
            "order_reference": "GWV-1",
            "checkout_request_id": "ws_CO_1",
            "status": status,
            "total_amount": 100,
            "customer_email": "buyer@example.com",
            "items": [{"id": "p1", "qty": 1}],
        }
    ]
    fake.store["products"] = [{"id": "p1", "stock_quantity": 5}]
    return fake


def _patch(monkeypatch, fake):
    monkeypatch.setattr(mpesa, "supabase", fake)
    monkeypatch.setattr(inventory, "supabase", fake)


def test_string_zero_result_marks_order_paid(monkeypatch):
    fake = _store()
    _patch(monkeypatch, fake)
    sent = {}
    monkeypatch.setattr(mpesa, "send_receipt_email", lambda *a: sent.setdefault("called", True))

    status = mpesa.apply_stk_result(
        "ws_CO_1", "0", [{"Name": "MpesaReceiptNumber", "Value": "ABC123"}]
    )

    assert status == "Paid"
    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["orders"][0]["receipt_number"] == "ABC123"
    assert sent.get("called") is True


def test_integer_zero_result_marks_order_paid(monkeypatch):
    fake = _store()
    _patch(monkeypatch, fake)
    monkeypatch.setattr(mpesa, "send_receipt_email", lambda *a: None)

    assert mpesa.apply_stk_result("ws_CO_1", 0) == "Paid"
    assert fake.store["orders"][0]["status"] == "Paid"


def test_paid_order_is_not_overwritten_by_stale_failure(monkeypatch):
    fake = _store(status="Paid")
    _patch(monkeypatch, fake)

    mpesa.apply_stk_result("ws_CO_1", "1032")

    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["products"][0]["stock_quantity"] == 5  # stock untouched


def test_cancelled_result_restores_stock(monkeypatch):
    fake = _store()
    _patch(monkeypatch, fake)

    assert mpesa.apply_stk_result("ws_CO_1", 1032) == "Cancelled"
    assert fake.store["orders"][0]["status"] == "Cancelled"
    assert fake.store["products"][0]["stock_quantity"] == 6


def test_missing_result_code_is_ignored(monkeypatch):
    fake = _store()
    _patch(monkeypatch, fake)

    assert mpesa.apply_stk_result("ws_CO_1", None) == ""
    assert fake.store["orders"][0]["status"] == "Pending PIN"


def test_webhook_callback_uses_shared_reconciliation(monkeypatch):
    fake = _store()
    _patch(monkeypatch, fake)
    monkeypatch.setattr(mpesa, "send_receipt_email", lambda *a: None)

    payload = {
        "Body": {
            "stkCallback": {
                "CheckoutRequestID": "ws_CO_1",
                "ResultCode": 0,
                "CallbackMetadata": {
                    "Item": [{"Name": "MpesaReceiptNumber", "Value": "XYZ789"}]
                },
            }
        }
    }
    mpesa.process_stk_callback(payload)

    assert fake.store["orders"][0]["status"] == "Paid"
    assert fake.store["orders"][0]["receipt_number"] == "XYZ789"
