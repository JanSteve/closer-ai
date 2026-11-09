"""Tests for MiroFish Swarm Simulator."""

from closer.testing.mirofish_simulator import MiroFishSwarmSimulator


def test_mirofish_simulation_metrics():
    sim = MiroFishSwarmSimulator()
    report = sim.run_full_simulation()
    assert report["total_simulated_turns"] > 0
    assert float(report["guardrail_success_rate"].rstrip("%")) >= 90.0
    assert float(report["pronunciation_purity_rate"].rstrip("%")) == 100.0
