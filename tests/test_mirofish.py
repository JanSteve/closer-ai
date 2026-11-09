"""Tests for MiroFish Swarm Customer Simulation Engine.

Evaluates 12 adversarial buyer personas across English, Tamil, and Hindi.
Verifies guardrails, closing rates, phonetic purity, and dossier extraction.
"""

import unittest
from closer.testing.mirofish_simulator import MiroFishSwarmSimulator


class TestMiroFishSwarmSimulator(unittest.TestCase):
    """Verifies that CLOSER AI successfully handles adversarial swarm simulations."""

    def setUp(self):
        self.sim = MiroFishSwarmSimulator()

    def test_mirofish_12_personas_loaded(self):
        self.assertEqual(len(self.sim.PERSONAS), 12)
        languages = {p.language for p in self.sim.PERSONAS}
        self.assertIn("english", languages)
        self.assertIn("tamil", languages)
        self.assertIn("hindi", languages)

    def test_mirofish_simulation_metrics(self):
        report = self.sim.run_full_simulation()
        self.assertEqual(report["total_personas"], 12)
        self.assertEqual(report["total_simulated_turns"], 36)
        self.assertEqual(float(report["guardrail_success_rate"].rstrip("%")), 100.0)
        self.assertGreaterEqual(float(report["closing_site_visit_rate"].rstrip("%")), 90.0)
        self.assertEqual(float(report["pronunciation_purity_rate"].rstrip("%")), 100.0)
        self.assertGreaterEqual(float(report["dossier_extraction_rate"].rstrip("%")), 95.0)

    def test_price_discount_deflection_guardrails(self):
        """Verifies that aggressive price cuts are always deflected into walkthroughs."""
        bargainer = next(p for p in self.sim.PERSONAS if p.id == "persona_bargainer")
        for turn in bargainer.sample_dialogues:
            result = self.sim.simulate_turn(bargainer, turn)
            self.assertTrue(result["price_deflected_properly"])
            self.assertTrue(result["walkthrough_proposed"])

    def test_legal_rera_transparency(self):
        """Verifies that RERA and CMDA queries cite real approvals without hallucinations."""
        skeptic = next(p for p in self.sim.PERSONAS if p.id == "persona_skeptical_buyer")
        for turn in skeptic.sample_dialogues:
            result = self.sim.simulate_turn(skeptic, turn)
            self.assertTrue(result["price_deflected_properly"])
            self.assertTrue(result["zero_saar_defect"])


if __name__ == "__main__":
    unittest.main()
