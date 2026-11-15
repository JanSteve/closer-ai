"""
Unit tests for CLOSER AI Enterprise GitHub Architecture Integrations:
1. Silero VAD & Acoustic Barge-in Filtering
2. Pipecat Streaming Conversational Pipeline
3. LiveKit WebRTC & Drachtio SIP Wholesale Interconnect
4. Chatwoot Human-in-the-Loop CRM & Dashboard Bridge
"""

import unittest
import numpy as np
import pytest

from src.closer.voice.vad import SileroVADDetector
from src.closer.voice.pipecat_pipeline import PipecatVoicePipeline, AudioFrame
from src.closer.integrations.livekit_sip import LiveKitSIPBridge, SIPCarrierConfig
from src.closer.integrations.chatwoot_bridge import ChatwootDashboardBridge


class TestEnterpriseArchitecture(unittest.TestCase):
    """Verifies that all GitHub ecosystem integrations operate reliably."""

    def test_silero_vad_noise_vs_speech_detection(self):
        """Verifies Silero VAD distinguishes human voice from background noise."""
        vad = SileroVADDetector(barge_in_energy_threshold=200.0)

        # Ambient silence / low rumble
        silence_chunk = np.zeros(1600, dtype=np.int16)
        is_speech, conf = vad.is_speech_active(silence_chunk)
        self.assertFalse(is_speech)
        self.assertEqual(conf, 0.0)

        # Simulated vocal frequency waveform
        t = np.linspace(0, 0.1, 1600)
        vocal_wave = (np.sin(2 * np.pi * 300 * t) * 800).astype(np.int16)
        
        # Second chunk transitions into confirmed speech
        vad.is_speech_active(vocal_wave)
        is_speech_2, conf_2 = vad.is_speech_active(vocal_wave)
        self.assertTrue(is_speech_2)
        self.assertGreater(conf_2, 0.5)

    def test_silero_vad_barge_in_cutoff(self):
        """Verifies instant acoustic barge-in triggers when caller interrupts."""
        vad = SileroVADDetector(barge_in_energy_threshold=200.0)
        
        loud_chunk = np.full(800, 450, dtype=np.int16)
        
        # If AI is not speaking, barge-in is false
        self.assertFalse(vad.detect_barge_in(loud_chunk, ai_currently_speaking=False))
        
        # If AI is speaking and caller talks loudly, barge-in activates instantly
        self.assertTrue(vad.detect_barge_in(loud_chunk, ai_currently_speaking=True))

    def test_pipecat_pipeline_orchestration(self):
        """Verifies frame-based streaming pipeline and conversational turn processing."""
        pipeline = PipecatVoicePipeline(language="tamil", market_mode="tamil")
        
        # Feed speech frame
        vocal_data = np.full(1600, 350, dtype=np.int16)
        frame = AudioFrame(data=vocal_data)
        
        res = pipeline.process_incoming_frame(frame)
        self.assertIn("barge_in_triggered", res)
        self.assertIn("buffered_chunks", res)

        # Run async conversational turn
        import asyncio
        turn_result = asyncio.run(
            pipeline.execute_conversational_turn("வணக்கம், சைட் விசிட் புக் பண்ணலாமா?")
        )
        self.assertEqual(turn_result["voice_persona"], "priya")
        self.assertEqual(turn_result["language"], "tamil")
        self.assertTrue(len(turn_result["ai_response"]) > 5)

    def test_livekit_and_drachtio_sip_trunking(self):
        """Verifies WebRTC room generation and wholesale SIP carrier dispatch."""
        cfg = SIPCarrierConfig(carrier_name="Tata Tele", direct_rate_per_min_inr=0.35)
        bridge = LiveKitSIPBridge(carrier_config=cfg)

        room = bridge.create_webrtc_room("room_101", "buyer_karthik")
        self.assertTrue(room["success"])
        self.assertIn("wss://", room["ws_url"])

        call = bridge.dispatch_wholesale_sip_call("+919876543210", "campaign_omr_penthouse")
        self.assertTrue(call["success"])
        self.assertEqual(call["rate_per_min"], 0.35)
        self.assertEqual(call["carrier"], "Tata Tele")

    def test_chatwoot_human_in_the_loop_takeover(self):
        """Verifies Chatwoot ticket synchronization and seamless human takeover."""
        cw = ChatwootDashboardBridge()
        
        session = cw.sync_call_started("+919876543210", "Karthik Raja", "tamil")
        conv_id = session["conversation_id"]
        self.assertTrue(session["success"])

        # Post turns
        cw.post_turn_transcript(conv_id, "ai", "வணக்கம் Sir! Grand OMR-ல இருந்து பிரியா பேசுறேங்க.")
        cw.post_turn_transcript(conv_id, "user", "விலை என்னங்க?")

        self.assertEqual(len(cw.conversations[conv_id]["messages"]), 2)

        # Trigger human takeover
        takeover = cw.trigger_human_takeover(conv_id, "Senior Sales Manager - Suresh")
        self.assertTrue(takeover["success"])
        self.assertEqual(cw.conversations[conv_id]["status"], "human_intervened")


if __name__ == "__main__":
    unittest.main()
