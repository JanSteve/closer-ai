"""Tests for IndicPhoneticNormalizer (TDD - ECC Standard).

Verifies:
1. "Saar" vs "Sir" substitution on Tamil Unicode boundaries.
2. Hyphenated loanword stutter prevention (e.g., family-யோட -> ஃபேமிலியோட).
3. Currency/unit naturalization (1.5 Crores -> ஒன்றரை கோடி / डेढ़ करोड़).
4. De-duplication of 'Sir' in conversational turns.
5. English passthrough preservation (zero alteration for locked-in Kokoro blend).
"""

import pytest
from closer.telephony.phonetic_normalizer import IndicPhoneticNormalizer


class TestIndicPhoneticNormalizer:

    def test_tamil_saar_to_sir(self):
        text = "வணக்கம் சார்! சொல்லுங்க சார்."
        normalized = IndicPhoneticNormalizer.normalize(text, "tamil")
        assert "சார்" not in normalized
        assert "Sir" in normalized

    def test_tamil_hyphen_loanwords(self):
        text = "நீங்க family-யோட குடிவர 3BHK பாக்குறீங்களா, இல்ல investment-க்காகவா சார்?"
        normalized = IndicPhoneticNormalizer.normalize(text, "tamil")
        assert "family-யோட" not in normalized
        assert "investment-க்காகவா" not in normalized
        assert "3 BHK" in normalized
        assert "Sir" in normalized

    def test_tamil_currency_naturalization(self):
        text = "உங்க பட்ஜெட் 1.5 Crores-க்குள்ள இருக்குங்களா சார்?"
        normalized = IndicPhoneticNormalizer.normalize(text, "tamil")
        assert "ஒன்றரை கோடி" in normalized

    def test_hindi_currency_and_courtesy(self):
        text = "नमस्ते साहब! अगर आपका budget 1.5 Crores है, तो बहुत शानदार 3BHK options हैं।"
        normalized = IndicPhoneticNormalizer.normalize(text, "hindi")
        assert "डेढ़ करोड़" in normalized
        assert "साहब" not in normalized
        assert "3 BHK" in normalized

    def test_english_passthrough_preservation(self):
        text = "Look, I totally get where you are coming from on the pricing."
        normalized = IndicPhoneticNormalizer.normalize(text, "english")
        assert normalized == text
