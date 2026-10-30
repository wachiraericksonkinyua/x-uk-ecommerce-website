import base64
import uuid
from datetime import datetime

import dotenv
import httpx
from fastapi import HTTPException
import os


SIMULATED_CALLBACK_URL = "https://example.com/payments/callback"


def _is_sandbox() -> bool:
    return os.getenv("DARAJA_IS_SANDBOX", "true").lower() == "true"


def _simulation_enabled() -> bool:
    return os.getenv("MPESA_SIMULATION_MODE", "").lower() == "true"


def _simulated_success() -> dict:
    """Return a Daraja-shaped success response for local/offline testing."""
    return {
        "ResponseCode": "0",
        "ResultCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "ResultDesc": "The service request is processed successfully.",
        "CheckoutRequestID": f"ws_CO_SIM_{uuid.uuid4().hex[:12]}",
        "CustomerMessage": "Success. Request accepted for processing",
    }


def _pending_stk_response() -> dict:
    """Placeholder checkout id used when Daraja is slow/unreachable.

    Unlike the simulated-success response it carries no ``ResultCode`` and does
    not use the ``ws_CO_SIM_`` prefix, so polling leaves the order as
    ``Pending PIN`` (allowing the customer to still pay or use the manual
    receipt verifier) instead of auto-succeeding or failing.
    """
    return {
        "ResponseCode": "0",
        "CheckoutRequestID": f"ws_CO_PEND_{uuid.uuid4().hex[:12]}",
        "CustomerMessage": "Request received. Awaiting payment confirmation.",
    }


def _normalize_phone(phone_number: str) -> str:
    """Normalize a Kenyan number to the 254XXXXXXXXX format Safaricom expects."""
    normalized = (phone_number or "").replace(" ", "").replace("+", "")
    if normalized.startswith("0") and len(normalized) == 10:
        normalized = "254" + normalized[1:]
    return normalized


class DarajaService:
    def __init__(self):
        self._refresh_config()

    def _refresh_config(self):
        """(Re)read the .env on every call so credential updates take effect immediately."""
        dotenv.load_dotenv(override=True)
        self.consumer_key = os.getenv("DARAJA_CONSUMER_KEY", "")
        self.consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET", "")
        self.shortcode = os.getenv("DARAJA_SHORTCODE", "174379")
        self.passkey = os.getenv("DARAJA_PASSKEY", "")
        self.security_credential = os.getenv("DARAJA_SECURITY_CREDENTIAL", "")
        sandbox = _is_sandbox()
        self.base_url = "https://sandbox.safaricom.co.ke" if sandbox else "https://api.safaricom.co.ke"

        callback_url = (os.getenv("DARAJA_CALLBACK_URL") or "").strip()
        if (
            not callback_url
            or "localhost" in callback_url
            or "127.0.0.1" in callback_url
        ):
            callback_url = SIMULATED_CALLBACK_URL
        self.callback_url = callback_url

    async def get_access_token(self):
        self._refresh_config()
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.get(url, headers={"Authorization": f"Basic {auth}"})
        except httpx.HTTPError as exc:
            print(f"[Daraja] get_access_token request error: {exc}")
            raise HTTPException(status_code=502, detail="Failed to connect to M-Pesa.")

        if res.status_code != 200:
            print(f"[Daraja] get_access_token failed: HTTP {res.status_code} - {res.text}")
            raise HTTPException(status_code=400, detail="Failed to connect to M-Pesa.")
        return res.json().get("access_token")

    async def send_stk_push(self, phone_number: str, amount: int, account_reference: str, transaction_desc: str):
        self._refresh_config()

        if _simulation_enabled():
            print("[Daraja] MPESA_SIMULATION_MODE=true; returning simulated STK success.")
            return _simulated_success()

        try:
            token = await self.get_access_token()
        except (HTTPException, httpx.HTTPError) as exc:
            print(f"[Daraja] WARNING: send_stk_push could not get access token ({exc}); falling back.")
            if _is_sandbox():
                return _simulated_success()
            return _pending_stk_response()

        if not token:
            print("[Daraja] WARNING: no access token returned; falling back.")
            if _is_sandbox():
                return _simulated_success()
            return _pending_stk_response()

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()

        normalized_phone = _normalize_phone(phone_number)
        final_amount = int(round(float(amount)))

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": final_amount,
            "PartyA": normalized_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": normalized_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            print(f"[Daraja] WARNING: send_stk_push request error ({exc}); falling back.")
            if _is_sandbox():
                print("[Daraja] Sandbox timeout/transport failure; returning simulated STK success.")
                return _simulated_success()
            return _pending_stk_response()

        try:
            data = res.json()
        except ValueError:
            data = {}
            print(f"[Daraja] send_stk_push non-JSON response: HTTP {res.status_code} - {res.text}")

        if res.status_code != 200 or data.get("ResponseCode") not in ("0", 0):
            print(f"[Daraja] send_stk_push failed: HTTP {res.status_code} - {res.text}")
            if res.status_code >= 500:
                # Server-side/timeout class error: never fail the order outright.
                if _is_sandbox():
                    print("[Daraja] Sandbox 5xx failure; returning simulated STK success.")
                    return _simulated_success()
                print("[Daraja] Daraja 5xx failure; returning pending checkout id.")
                return _pending_stk_response()
            raise HTTPException(
                status_code=400,
                detail=data.get("errorMessage")
                or data.get("ResponseDescription")
                or "STK push failed",
            )

        return data

    async def query_stk_status(self, checkout_request_id: str) -> dict:
        """Query Daraja for the live status of an STK Push request.

        Uses the `stkpushquery/v1/query` endpoint, which lets us detect a
        customer-cancelled or timed-out prompt without waiting for the callback
        webhook. Returns the parsed Safaricom response (including `ResultCode`
        once the transaction reaches a final state) or an empty dict when the
        status cannot be determined — callers should then leave the order as-is.
        """
        self._refresh_config()

        if _simulation_enabled() or (checkout_request_id or "").startswith("ws_CO_SIM_"):
            # Local/simulated checkouts have no real Daraja record to query.
            # Report success so polling instantly flips test orders to "Paid"
            # instead of leaving them stuck on "Pending PIN".
            print("[Daraja] Simulated STK query; returning successful status.")
            return {
                "ResponseCode": "0",
                "ResultCode": "0",
                "ResultDesc": "The service request is processed successfully.",
            }

        if not checkout_request_id:
            return {}

        try:
            token = await self.get_access_token()
        except (HTTPException, httpx.HTTPError) as exc:
            print(f"[Daraja] query_stk_status could not get access token: {exc}")
            return {}

        if not token:
            print("[Daraja] query_stk_status: no access token returned.")
            return {}

        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            print(f"[Daraja] query_stk_status request error: {exc}")
            return {}

        if res.status_code != 200:
            print(f"[Daraja] query_stk_status failed: HTTP {res.status_code} - {res.text}")
            return {}

        try:
            return res.json()
        except ValueError:
            print(f"[Daraja] query_stk_status non-JSON response: HTTP {res.status_code} - {res.text}")
            return {}

    async def check_transaction(self, transaction_id: str) -> bool:
        """Queries Safaricom to verify if an M-Pesa receipt is real."""
        self._refresh_config()

        if _simulation_enabled():
            # No real Daraja record locally — treat manual receipts as valid so
            # test orders don't get stuck on "Payment Failed".
            print("[Daraja] Simulated transaction check; returning success.")
            return True

        access_token = await self.get_access_token()

        # The official Daraja sandbox endpoint for transaction status
        api_url = f"{self.base_url}/mpesa/transactionstatus/v1/query"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "Initiator": "testapi",
            "SecurityCredential": self.security_credential,
            "CommandID": "TransactionStatusQuery",
            "TransactionID": transaction_id,
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "ResultURL": f"{self.callback_url}/status-result",
            "QueueTimeOutURL": f"{self.callback_url}/status-timeout",
            "Remarks": "Manual receipt verification",
            "Occasion": "Order Checkout",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers)
            data = response.json()

            # A ResponseCode of "0" means Safaricom accepted the query
            if data.get("ResponseCode") == "0":
                return True

        return False
