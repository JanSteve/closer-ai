"""
Unit tests for CLOSER AI APILayer Unified Suite & Public-APIs Integration.
Validates Numverify (phone & carrier), Mailboxlayer (email deliverability),
Positionstack (property geocoding), and Fixer / Currencylayer (real estate FX).
"""

import unittest
from unittest.mock import patch, MagicMock
import io
import json

from src.closer.integrations.apilayer import APILayerUnifiedClient


class TestAPILayerUnifiedSuite(unittest.TestCase):
    """Test suite for APILayer Unified Suite and Public APIs integration."""

    def setUp(self):
        self.client = APILayerUnifiedClient()

    def test_phone_verification_usa_carrier(self):
        """Verifies US number validation resolves carrier and line type."""
        result = self.client.verify_phone("+1-310-555-0144")
        self.assertTrue(result["valid"])
        self.assertEqual(result["country_code"], "US")
        self.assertEqual(result["line_type"], "mobile")
        self.assertIn("Verizon", result["carrier"])
        self.assertIn("Beverly Hills", result["location"])

    def test_phone_verification_india_carrier(self):
        """Verifies Indian number validation resolves telecom network (Jio / Airtel)."""
        result = self.client.verify_phone("+91-98800-12345")
        self.assertTrue(result["valid"])
        self.assertEqual(result["country_code"], "IN")
        self.assertIn("India", result["country_name"])
        self.assertTrue("Jio" in result["carrier"] or "Airtel" in result["carrier"])

    def test_email_verification_corporate_vs_free(self):
        """Verifies corporate executive email vs free consumer email classification."""
        corp_result = self.client.verify_email("steve@danielrealty.com")
        self.assertTrue(corp_result["valid"])
        self.assertTrue(corp_result["is_corporate"])
        self.assertGreaterEqual(corp_result["score"], 0.90)

        free_result = self.client.verify_email("buyer@gmail.com")
        self.assertTrue(free_result["valid"])
        self.assertFalse(free_result["is_corporate"])

        invalid_result = self.client.verify_email("notanemail")
        self.assertFalse(invalid_result["valid"])

    def test_property_geocoding_bel_air_and_bangalore(self):
        """Verifies spatial geocoding for luxury corridors in Los Angeles and Bengaluru."""
        # Bel Air
        us_res = self.client.geocode_property("10484 Bellagio Rd, Bel Air, CA")
        self.assertTrue(us_res["found"])
        self.assertEqual(us_res["country"], "USA")
        self.assertAlmostEqual(us_res["latitude"], 34.0837, places=2)
        self.assertIn("Bel Air", us_res["neighborhood_tier"])

        # Bangalore Whitefield
        in_res = self.client.geocode_property("Prestige Lakeside Habitat, Whitefield, Bengaluru")
        self.assertTrue(in_res["found"])
        self.assertEqual(in_res["country"], "India")
        self.assertAlmostEqual(in_res["latitude"], 12.9698, places=2)
        self.assertIn("K-RERA", in_res["rera_jurisdiction"])

    def test_currency_conversion_usd_to_inr_crores(self):
        """Verifies USD to INR conversion returns accurate real estate Crores notation."""
        res = self.client.convert_currency(6850000, from_curr="USD", to_curr="INR")
        self.assertEqual(res["from_currency"], "USD")
        self.assertEqual(res["to_currency"], "INR")
        self.assertGreater(res["converted_amount"], 500000000)  # > 50 Cr
        self.assertIn("Crores", res["real_estate_notation"])

    def test_currency_conversion_inr_to_usd_millions(self):
        """Verifies INR ₹2.45 Crores converts to USD Millions notation."""
        res = self.client.convert_currency(24500000, from_curr="INR", to_curr="USD")
        self.assertEqual(res["from_currency"], "INR")
        self.assertEqual(res["to_currency"], "USD")
        self.assertGreater(res["converted_amount"], 250000)
        self.assertIn("Million", res["real_estate_notation"])

    def test_360_lead_dossier_enrichment(self):
        """Verifies end-to-end 360-degree client dossier enrichment."""
        dossier = {
            "full_name": "Victoria Sterling",
            "phone_number": "+1-310-555-0188",
            "email": "vsterling@sterlingcapital.com",
            "property_type": "10484 Bellagio Rd, Bel Air, CA",
            "budget_max": 8500000,
            "market_region": "USA"
        }
        enriched = self.client.enrich_lead_dossier(dossier)
        self.assertIn("phone_intelligence", enriched)
        self.assertIn("email_intelligence", enriched)
        self.assertIn("spatial_intelligence", enriched)
        self.assertIn("fx_intelligence", enriched)
        self.assertEqual(enriched["status"], "Enriched & Validated")
        self.assertTrue(enriched["phone_intelligence"]["valid"])
        self.assertTrue(enriched["email_intelligence"]["is_corporate"])


if __name__ == "__main__":
    unittest.main()
