"""Update the Twilio phone number's voice webhook URL.

Usage:
    uv run python scripts/update_twilio_webhook.py
    uv run python scripts/update_twilio_webhook.py https://your-tunnel.trycloudflare.com

If no URL is provided, reads APP_BASE_URL from .env.
"""

import sys

from twilio.rest import Client

from config import settings


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else settings.app_base_url
    voice_url = f"{base_url}/webhook/voice/outbound"

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    # Find the phone number SID
    numbers = client.incoming_phone_numbers.list(phone_number=settings.twilio_phone_number)
    if not numbers:
        print(f"No Twilio number found matching {settings.twilio_phone_number}")
        sys.exit(1)

    number = numbers[0]
    number.update(voice_url=voice_url, voice_method="POST")
    print(f"Updated {settings.twilio_phone_number} voice webhook to: {voice_url}")


if __name__ == "__main__":
    main()
