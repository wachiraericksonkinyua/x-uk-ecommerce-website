import base64
from datetime import datetime
import dotenv
import httpx
from fastapi import HTTPException
import os
import dotenv

dotenv.load_dotenv()

class DarajaService:
    def __init__(self):
        self.consumer_key = os.getenv("DARAJA_CONSUMER_KEY", "")
        self.consumer_secret = os.getenv("DARAJA_CONSUMER_SECRET", "")
        self.shortcode = os.getenv("DARAJA_SHORTCODE", "174379")
        self.passkey = os.getenv("DARAJA_PASSKEY", "")
        self.callback_url = os.getenv("DARAJA_CALLBACK_URL", "")
        sandbox = os.getenv("DARAJA_IS_SANDBOX", "true").lower() == "true"
        self.base_url = "https://sandbox.safaricom.co.ke" if sandbox else "https://api.safaricom.co.ke"

    async def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers={"Authorization": f"Basic {auth}"})
            if res.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to connect to M-Pesa.")
            return res.json().get("access_token")

    async def send_stk_push(self, phone_number: str, amount: int, account_reference: str, transaction_desc: str):
        token = await self.get_access_token()
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{self.shortcode}{self.passkey}{timestamp}".encode()).decode()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
            data = res.json()
            if res.status_code != 200 or data.get("ResponseCode") not in ("0", 0):
                raise HTTPException(status_code=400, detail=data.get("errorMessage") or data.get("ResponseDescription") or "STK push failed")
            return data