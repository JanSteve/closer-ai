"""
Configuration management for CLOSER AI — Amura Health / Amura AI Clinical Voice Platform.
Supports environment variables, .env file loading, and typed settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


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
    """Production settings for CLOSER AI Clinical & Hospital Front-Desk Runtime."""

    # Platform Identity
    FOUNDER_NAME: str = "R Jan Steve Daniel"
    PROJECT_NAME: str = "CLOSER AI"
    VERSION: str = "2.0.0"
    GITHUB_REPO: str = "https://github.com/JanSteve/closer-ai"
    PORTFOLIO_URL: str = "https://www.stevedaniel.me"

    # LLM Settings (Gemini, Groq, OpenAI, OpenRouter)
    GEMINI_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )
    GROQ_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    OPENAI_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    OPENROUTER_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    OPENAI_API_BASE: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_BASE"))
    LLM_MODEL: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"))
    LLM_TEMPERATURE: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))

    # Voice Synthesis & Audio Settings
    SARVAM_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("SARVAM_API_KEY"))
    SARVAM_TTS_MODEL: str = field(default_factory=lambda: os.getenv("SARVAM_TTS_MODEL", "bulbul:v3"))
    ELEVENLABS_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY"))
    CARTESIA_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("CARTESIA_API_KEY"))
    DEFAULT_VOICE: str = field(default_factory=lambda: os.getenv("DEFAULT_VOICE", "en-IN-NeerjaExpressiveNeural"))
    FALLBACK_VOICE: str = field(default_factory=lambda: os.getenv("FALLBACK_VOICE", "en-US-AvaNeural"))
    SPEECH_RATE: str = field(default_factory=lambda: os.getenv("SPEECH_RATE", "+4%"))
    AUDIO_SAMPLE_RATE: int = field(default_factory=lambda: int(os.getenv("AUDIO_SAMPLE_RATE", "24000")))

    # Telephony & Webhooks
    TWILIO_ACCOUNT_SID: Optional[str] = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID"))
    TWILIO_AUTH_TOKEN: Optional[str] = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN"))
    TWILIO_PHONE_NUMBER: str = field(default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", "+916262262222"))

    # Amura Health / Amura AI Clinical Identity (Velachery, Chennai)
    CLINIC_NAME: str = field(default_factory=lambda: os.getenv("CLINIC_NAME", "Amura Health"))
    CLINIC_BRAND_ALT: str = "Amura AI"
    CLINIC_ADDRESS: str = field(
        default_factory=lambda: os.getenv(
            "CLINIC_ADDRESS",
            "11th Floor, One National Park, 142 Velachery Main Road, Chennai - 600042",
        )
    )
    CLINIC_PHONE: str = field(default_factory=lambda: os.getenv("CLINIC_PHONE", "+91-62-622-62222"))
    CLINIC_EMAIL: str = field(default_factory=lambda: os.getenv("CLINIC_EMAIL", "care@amura.ai"))
    CLINICAL_DIRECTOR_NAME: str = field(
        default_factory=lambda: os.getenv("CLINICAL_DIRECTOR_NAME", "Dr. Godwin Samuel Christudas & Amura Care Team")
    )
    CLINICAL_TITLE: str = "Amura Health Clinical Care Team"
    CLINICAL_SPECIALTIES: str = (
        "Type-2 Diabetes, Pre-Diabetes, Insulin Resistance, Hypertension, Dyslipidemia, "
        "PCOD/PCOS, Thyroid, Fatty Liver, Obesity, Gut Health"
    )
    EMERGENCY_HELPLINE: str = "108"

    # Calendar & Booking
    GOOGLE_CALENDAR_ID: str = field(default_factory=lambda: os.getenv("GOOGLE_CALENDAR_ID", "primary"))
    GOOGLE_SERVICE_ACCOUNT_JSON: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/service_account.json")
    )
    BOOKING_TIMEZONE: str = field(default_factory=lambda: os.getenv("BOOKING_TIMEZONE", "Asia/Kolkata"))
    CONSULT_DURATION_MINUTES: int = field(default_factory=lambda: int(os.getenv("CONSULT_DURATION_MINUTES", "30")))
    BUFFER_MINUTES: int = field(default_factory=lambda: int(os.getenv("BUFFER_MINUTES", "15")))

    # Clinical CRM & Webhooks
    CRM_API_KEY: Optional[str] = field(
        default_factory=lambda: os.getenv("CRM_API_KEY") or os.getenv("FOLLOW_UP_BOSS_API_KEY")
    )
    CRM_WEBHOOK_URL: Optional[str] = field(default_factory=lambda: os.getenv("CRM_WEBHOOK_URL"))
    WEBHOOK_SECRET: str = field(default_factory=lambda: os.getenv("WEBHOOK_SECRET", "closer_ai_dev_secret_2026"))

    # APILayer Unified Suite
    APILAYER_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("APILAYER_API_KEY"))

    # Server Runtime
    HOST: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"))

    # Transitional compatibility aliases (all return Amura Health clinical values)
    @property
    def CLINICIAN_NAME(self) -> str:
        return self.CLINICAL_DIRECTOR_NAME

    @property
    def BROKERAGE_NAME(self) -> str:
        return self.CLINIC_NAME

    @property
    def REALTOR_NAME(self) -> str:
        return self.CLINICAL_DIRECTOR_NAME

    @property
    def REALTOR_TITLE(self) -> str:
        return self.CLINICAL_TITLE

    @property
    def REALTOR_PHONE(self) -> str:
        return self.CLINIC_PHONE

    @property
    def REALTOR_EMAIL(self) -> str:
        return self.CLINIC_EMAIL

    @property
    def PRIMARY_MARKETS(self) -> str:
        return "Velachery Chennai, Online Metabolic Care (India & Global)"

    @property
    def TOUR_DURATION_MINUTES(self) -> int:
        return self.CONSULT_DURATION_MINUTES

    @property
    def FOLLOW_UP_BOSS_API_KEY(self) -> Optional[str]:
        return self.CRM_API_KEY

    def to_dict(self) -> Dict[str, Any]:
        """Export settings dict excluding sensitive credentials."""
        return {
            "PROJECT_NAME": self.PROJECT_NAME,
            "VERSION": self.VERSION,
            "FOUNDER_NAME": self.FOUNDER_NAME,
            "DEFAULT_VOICE": self.DEFAULT_VOICE,
            "FALLBACK_VOICE": self.FALLBACK_VOICE,
            "AUDIO_SAMPLE_RATE": self.AUDIO_SAMPLE_RATE,
            "CLINIC_NAME": self.CLINIC_NAME,
            "CLINIC_ADDRESS": self.CLINIC_ADDRESS,
            "CLINIC_PHONE": self.CLINIC_PHONE,
            "CLINIC_EMAIL": self.CLINIC_EMAIL,
            "CLINICAL_DIRECTOR_NAME": self.CLINICAL_DIRECTOR_NAME,
            "CLINICAL_SPECIALTIES": self.CLINICAL_SPECIALTIES,
            "EMERGENCY_HELPLINE": self.EMERGENCY_HELPLINE,
            "BOOKING_TIMEZONE": self.BOOKING_TIMEZONE,
            "CONSULT_DURATION_MINUTES": self.CONSULT_DURATION_MINUTES,
            "SARVAM_TTS_MODEL": self.SARVAM_TTS_MODEL,
            "HAS_GEMINI_KEY": bool(self.GEMINI_API_KEY),
            "HAS_GROQ_KEY": bool(self.GROQ_API_KEY),
            "HAS_SARVAM_KEY": bool(self.SARVAM_API_KEY),
            "HAS_TWILIO_CONFIG": bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN),
            "HAS_CRM_CONFIG": bool(self.CRM_API_KEY),
            "HAS_APILAYER_KEY": bool(self.APILAYER_API_KEY),
        }


settings = Settings()
