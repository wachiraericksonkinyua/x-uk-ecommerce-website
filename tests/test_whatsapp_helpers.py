import hashlib
import hmac

import app.services.whatsapp as whatsapp


def test_status_from_score(monkeypatch):
    monkeypatch.setattr(whatsapp, "HOT_THRESHOLD", 70)
    monkeypatch.setattr(whatsapp, "WARM_THRESHOLD", 40)

    assert whatsapp._status_from_score(90) == "hot"
    assert whatsapp._status_from_score(70) == "hot"
    assert whatsapp._status_from_score(50) == "warm"
    assert whatsapp._status_from_score(10) == "cold"


def test_parse_plain_json():
    reply, meta = whatsapp._parse_model_output('{"reply": "hi", "score": 80}')
    assert reply == "hi"
    assert meta["score"] == 80


def test_parse_json_inside_code_fence():
    raw = '```json\n{"reply": "yo", "score": 10}\n```'
    reply, meta = whatsapp._parse_model_output(raw)
    assert reply == "yo"
    assert meta["score"] == 10


def test_parse_falls_back_to_raw_text():
    reply, meta = whatsapp._parse_model_output("just some text")
    assert reply == "just some text"
    assert meta == {}


def test_extract_inbound_message():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"profile": {"name": "Test Buyer"}}],
                            "messages": [
                                {
                                    "from": "254700000000",
                                    "id": "wamid.TEST",
                                    "type": "text",
                                    "text": {"body": "Hello"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    message = whatsapp.extract_inbound_message(payload)
    assert message == {"from": "254700000000", "text": "Hello", "id": "wamid.TEST", "name": "Test Buyer"}


def test_extract_inbound_message_returns_none_for_statuses():
    assert whatsapp.extract_inbound_message({"entry": [{"changes": [{"value": {}}]}]}) is None


def test_verify_signature_with_secret(monkeypatch):
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "s3cr3t")
    body = b'{"a":1}'
    valid = "sha256=" + hmac.new(b"s3cr3t", body, hashlib.sha256).hexdigest()

    assert whatsapp.verify_signature(body, valid) is True
    assert whatsapp.verify_signature(body, "sha256=deadbeef") is False
    assert whatsapp.verify_signature(body, None) is False


def test_verify_signature_skipped_when_unconfigured(monkeypatch):
    monkeypatch.delenv("WHATSAPP_APP_SECRET", raising=False)
    assert whatsapp.verify_signature(b"anything", None) is True
