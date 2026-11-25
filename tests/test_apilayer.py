"""
Unit tests for CLOSER AI APILayer Unified Suite Integration (Amura Health Clinical Context).
Validates Numverify (patient phone), Mailboxlayer (email deliverability),
Positionstack (Velachery Chennai clinic geocoding), Fixer (healthcare FX), and mocked live HTTP.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from src.closer.integrations.apilayer import APILayerUnifiedClient


class TestAPILayerUnifiedSuite(unittest.TestCase):
    """Test suite for APILayer Unified Suite integration."""

    def setUp(self):
        self._env_patch = patch.dict(os.environ, {"APILAYER_API_KEY": ""})
        self._env_patch.start()
        self.client = APILayerUnifiedClient(api_key="")

    def tearDown(self):
        self._env_patch.stop()

    def test_phone_verification_usa_carrier(self):
        result = self.client.verify_phone("+1-310-555-0144")
        self.assertTrue(result["valid"])
        self.assertEqual(result["country_code"], "US")
        self.assertEqual(result["line_type"], "mobile")
        self.assertIn("Verizon", result["carrier"])

    def test_phone_verification_india_chennai_carrier(self):
        result = self.client.verify_phone("+91-98400-12345")
        self.assertTrue(result["valid"])
        self.assertEqual(result["country_code"], "IN")
        self.assertIn("India", result["country_name"])
        self.assertIn("Chennai", result["location"])
        self.assertTrue("Jio" in result["carrier"] or "Airtel" in result["carrier"])

    def test_email_verification_corporate_vs_free(self):
        corp_result = self.client.verify_email("care@amura.ai")
        self.assertTrue(corp_result["valid"])
        self.assertTrue(corp_result["is_corporate"])
        self.assertGreaterEqual(corp_result["score"], 0.90)

        free_result = self.client.verify_email("patient@gmail.com")
        self.assertTrue(free_result["valid"])
        self.assertFalse(free_result["is_corporate"])

        invalid_result = self.client.verify_email("notanemail")
        self.assertFalse(invalid_result["valid"])

    def test_clinic_geocoding_velachery_chennai_and_bengaluru(self):
        """Verifies spatial geocoding for Amura Health Velachery Chennai and partner telehealth hubs."""
        chennai_res = self.client.geocode_clinic_address("142 Velachery Main Road, Chennai 600042")
        self.assertTrue(chennai_res["found"])
        self.assertEqual(chennai_res["country"], "India")
        self.assertEqual(chennai_res["postal_code"], "600042")
        self.assertAlmostEqual(chennai_res["latitude"], 12.9915, places=2)
        self.assertIn("Velachery", chennai_res["care_zone"])

        # Transitional alias geocode_property still delegates cleanly without real-estate labels
        blr_res = self.client.geocode_property("Indiranagar, Bengaluru")
        self.assertTrue(blr_res["found"])
        self.assertEqual(blr_res["country"], "India")
        self.assertIn("Telehealth", blr_res["care_zone"])
        self.assertNotIn("rera_jurisdiction", blr_res)

    def test_currency_conversion_usd_to_inr_care_plan(self):
        """Verifies USD to INR healthcare care-plan conversion returns Lakhs/Crores notation."""
        res = self.client.convert_currency(1500, from_curr="USD", to_curr="INR")
        self.assertEqual(res["from_currency"], "USD")
        self.assertEqual(res["to_currency"], "INR")
        self.assertGreater(res["converted_amount"], 100000)
        self.assertIn("Lakhs", res["healthcare_notation"])
        self.assertNotIn("real_estate_notation", res)

    def test_currency_conversion_inr_to_usd(self):
        res = self.client.convert_currency(125000, from_curr="INR", to_curr="USD")
        self.assertEqual(res["from_currency"], "INR")
        self.assertEqual(res["to_currency"], "USD")
        self.assertGreater(res["converted_amount"], 1000)
        self.assertIn("USD", res["healthcare_notation"])

    def test_360_patient_dossier_enrichment(self):
        dossier = {
            "patient_name": "Priya Raman",
            "phone_number": "+91-98400-11223",
            "email": "care@amura.ai",
            "clinic_location": "142 Velachery Main Road, Chennai - 600042",
            "budget_max": 125000,
            "market_region": "INDIA",
        }
        enriched = self.client.enrich_patient_dossier(dossier)
        self.assertIn("phone_intelligence", enriched)
        self.assertIn("email_intelligence", enriched)
        self.assertIn("spatial_intelligence", enriched)
        self.assertIn("fx_intelligence", enriched)
        self.assertEqual(enriched["status"], "Enriched & Validated")
        self.assertTrue(enriched["phone_intelligence"]["valid"])
        self.assertTrue(enriched["email_intelligence"]["is_corporate"])
        self.assertEqual(enriched["spatial_intelligence"]["postal_code"], "600042")

    def test_mocked_live_apilayer_response(self):
        """Verifies live APILayer JSON parsing without issuing network calls."""
        live_client = APILayerUnifiedClient(api_key="test_apilayer_live_key_123")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "valid": True,
                "international_format": "+919840012345",
                "country_name": "India",
                "country_code": "IN",
                "location": "Chennai",
                "carrier": "Airtel",
                "line_type": "mobile",
            }
        ).encode("utf-8")
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_resp
        mock_ctx.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_ctx) as mock_open:
            res = live_client.verify_phone("+91-98400-12345")
            self.assertTrue(res["valid"])
            self.assertEqual(res["provider"], "APILayer Numverify (Live)")
            mock_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
