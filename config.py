from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Twilio (voice only)
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Telegram
    telegram_bot_token: str

    # Gemini (used for embeddings + browser-use)
    gemini_api_key: str

    # Scrappa (flights/hotels/shopping search)
    scrappa_api_key: str

    # Browser Use (optional — optimized browser automation model)
    browser_use_api_key: str = ""

    # Cartesia
    cartesia_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # App
    app_base_url: str
    host: str = "0.0.0.0"
    port: int = 8000

    # Call settings
    call_input_timeout_seconds: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
