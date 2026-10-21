"""
Configuration management for CLOSER AI.
Supports environment variables, .env file loading, and typed settings.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Load .env if present
def _load_env_file() -> None:
    env_path = Path(".env")
    if not env_path.is_file():
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    
    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()


@dataclass
class Settings:
    """Production settings for CLOSER AI runtime."""
    
    # Founder & Platform Identity
    FOUNDER_NAME: str = "R Jan Steve Daniel"
    PROJECT_NAME: str = "CLOSER AI"
    VERSION: str = "1.0.0"
    GITHUB_REPO: str = "https://github.com/JanSteve/closer-ai"
    PORTFOLIO_URL: str = "https://www.stevedaniel.me"
    
    # LLM Settings
    GROQ_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    LLM_MODEL: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"))
    LLM_TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    
    # Voice Synthesis & Audio Settings
    DEFAULT_VOICE: str = field(default_factory=lambda: os.getenv("DEFAULT_VOICE", "en-US-GuyNeural"))
    FALLBACK_VOICE: str = field(default_factory=lambda: os.getenv("FALLBACK_VOICE", "en-US-AriaNeural"))
    SPEECH_RATE: str = field(default_factory=lambda: os.getenv("SPEECH_RATE", "+7%"))
    AUDIO_SAMPLE_RATE: int = field(default_factory=lambda: int(os.getenv("AUDIO_SAMPLE_RATE", "24000")))
    
    # Telephony & Webhooks
    TWILIO_ACCOUNT_SID: Optional[str] = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID"))
    TWILIO_AUTH_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN"))
    TWILIO_PHONE_NUMBER: str = field(default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", "+13105550199"))
    
    # Real Estate Brokerage Identity
    BROKERAGE_NAME: str = field(default_factory=lambda: os.getenv("BROKERAGE_NAME", "Daniel & Associates Luxury Realty"))
    REALTOR_NAME: str = field(default_factory=lambda: os.getenv("REALTOR_NAME", "R Jan Steve Daniel"))
    REALTOR_TITLE: str = field(default_factory=lambda: os.getenv("REALTOR_TITLE", "Principal Luxury Real Estate Broker"))
    REALTOR_PHONE: str = field(default_factory=lambda: os.getenv("REALTOR_PHONE", "+1-310-555-0199"))
    REALTOR_EMAIL: str = field(default_factory=lambda: os.getenv("REALTOR_EMAIL", "steve@danielrealty.com"))
    PRIMARY_MARKETS: str = field(default_factory=lambda: os.getenv("PRIMARY_MARKETS", "Beverly Hills, Bel Air, Malibu, Holmby Hills, Tribeca"))
    
    # Calendar & Booking
    GOOGLE_CALENDAR_ID: str = field(default_factory=lambda: os.getenv("GOOGLE_CALENDAR_ID", "primary"))
    GOOGLE_SERVICE_ACCOUNT_JSON: str = field(default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/service_account.json"))
    BOOKING_TIMEZONE: str = field(default_factory=lambda: os.getenv("BOOKING_TIMEZONE", "America/Los_Angeles"))
    TOUR_DURATION_MINUTES: int = field(default_factory=lambda: int(os.getenv("TOUR_DURATION_MINUTES", "45")))
    BUFFER_MINUTES: int = field(default_factory=lambda: int(os.getenv("BUFFER_MINUTES", "15")))
    
    # CRM & Webhooks
    FOLLOW_UP_BOSS_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("FOLLOW_UP_BOSS_API_KEY"))
    CRM_WEBHOOK_URL: Optional[str] = field(default_factory=lambda: os.getenv("CRM_WEBHOOK_URL"))
    WEBHOOK_SECRET: str = field(default_factory=lambda: os.getenv("WEBHOOK_SECRET", "closer_ai_dev_secret_2026"))
    
    # APILayer Unified Suite / Public-APIs Integration
    APILAYER_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("APILAYER_API_KEY"))
    
    # Server Runtime
    HOST: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Export settings dict excluding sensitive credentials."""
        return {
            "PROJECT_NAME": self.PROJECT_NAME,
            "VERSION": self.VERSION,
            "FOUNDER_NAME": self.FOUNDER_NAME,
            "DEFAULT_VOICE": self.DEFAULT_VOICE,
            "FALLBACK_VOICE": self.FALLBACK_VOICE,
            "AUDIO_SAMPLE_RATE": self.AUDIO_SAMPLE_RATE,
            "BROKERAGE_NAME": self.BROKERAGE_NAME,
            "REALTOR_NAME": self.REALTOR_NAME,
            "PRIMARY_MARKETS": self.PRIMARY_MARKETS,
            "BOOKING_TIMEZONE": self.BOOKING_TIMEZONE,
            "TOUR_DURATION_MINUTES": self.TOUR_DURATION_MINUTES,
            "HAS_GROQ_KEY": bool(self.GROQ_API_KEY),
            "HAS_TWILIO_CONFIG": bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN),
            "HAS_FUB_CONFIG": bool(self.FOLLOW_UP_BOSS_API_KEY),
            "HAS_APILAYER_KEY": bool(self.APILAYER_API_KEY)
        }

settings = Settings()
