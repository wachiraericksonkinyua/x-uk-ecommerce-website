#!/usr/bin/env python3
"""Create or reset an admin account for the X-UK dashboard.

Uses the Supabase service-role key from `.env`, so run it from the repo root:

    venv/bin/python scripts/reset_admin_password.py --generate
    venv/bin/python scripts/reset_admin_password.py --email you@example.com --password 'NewStrongPass1!'

The script:
  1. finds the auth user by email (or creates one, pre-confirmed),
  2. sets a new password,
  3. makes sure the matching `profiles` row is flagged as admin.

Never commit the generated password. Change it after logging in.
"""

from __future__ import annotations

import argparse
import os
import secrets
import string
import sys

from dotenv import load_dotenv


def _admin_emails() -> list[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return [email.strip() for email in raw.split(",") if email.strip()]


def _generate_password(length: int = 18) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    # Guarantee at least one of each class.
    required = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*-_=+"),
    ]
    rest = [secrets.choice(alphabet) for _ in range(max(0, length - len(required)))]
    password = required + rest
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def main() -> int:
    load_dotenv(".env")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Admin email (defaults to first ADMIN_EMAILS entry)")
    parser.add_argument("--password", help="New password (omit with --generate)")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a strong random temporary password",
    )
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_KEY in .env", file=sys.stderr)
        return 1

    from supabase import create_client

    email = (args.email or "").strip()
    if not email:
        candidates = _admin_emails()
        if len(candidates) != 1:
            print(
                "ADMIN_EMAILS has multiple (or zero) entries; pass --email explicitly.",
                file=sys.stderr,
            )
            if candidates:
                print("Candidates: " + ", ".join(candidates), file=sys.stderr)
            return 1
        email = candidates[0]

    password = args.password
    generated = False
    if not password:
        if not args.generate:
            print("Pass --password or --generate.", file=sys.stderr)
            return 1
        password = _generate_password()
        generated = True

    client = create_client(url, key)

    try:
        users = client.auth.admin.list_users()
    except Exception as exc:  # pragma: no cover - depends on live credentials
        print(f"Could not list auth users: {exc}", file=sys.stderr)
        return 1

    user = next(
        (u for u in users if (getattr(u, "email", "") or "").lower() == email.lower()),
        None,
    )

    try:
        if user is None:
            created = client.auth.admin.create_user(
                {"email": email, "password": password, "email_confirm": True}
            )
            user = created.user
            action = "created"
        else:
            client.auth.admin.update_user_by_id(
                user.id, {"password": password, "email_confirm": True}
            )
            action = "updated"
    except Exception as exc:  # pragma: no cover - depends on live credentials
        print(f"Could not {action if 'action' in locals() else 'write'} account: {exc}", file=sys.stderr)
        return 1

    uid = user.id

    # Keep the profile in sync so `require_admin` recognises the account even
    # without the ADMIN_EMAILS allowlist.
    profile_payload = {"user_id": uid, "role": "admin", "is_admin": True}
    for column in ("user_id", "id"):
        try:
            existing = (
                client.table("profiles").select("id").eq(column, uid).limit(1).execute()
            )
            if existing.data:
                client.table("profiles").update(
                    {"role": "admin", "is_admin": True}
                ).eq(column, uid).execute()
            else:
                client.table("profiles").insert(
                    {**profile_payload, "id": uid}
                ).execute()
            break
        except Exception as exc:
            print(f"[profile] {column} update skipped: {exc}", file=sys.stderr)

    print(f"Admin account {action}: {email}")
    print(f"User id: {uid}")
    if generated:
        print(f"Temporary password: {password}")
        print("Log in at http://localhost:5174 and change it immediately.")
    else:
        print("Password updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
