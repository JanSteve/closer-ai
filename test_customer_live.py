"""Interactive Customer Testing Simulator for CLOSER AI.

Tri-Lingual Testing Sandbox (One Premium Female Closer per Language):
- 1. 🇺🇸 English: Signature CLOSER AI (Kokoro 3-Way SOTA Blend — Locked in)
- 2. 🇮🇳 Tamil: பல்லவி (Pallavi — Natural Tanglish Female Closer, TN Dialect)
- 3. 🇮🇳 Hindi: स्वाति (Swati — Natural Hinglish Female Closer, Telecaller Cadence)

100% Free, Zero API keys, Zero cost, runs locally on your Mac.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import tempfile
import time

from closer.qualification.extractor import QualificationExtractor
from closer.telephony.fallback import HallucinationDeflector
from closer.voice_engine import NeuralVoiceEngine, VOICE_PROFILES


class CustomerTestingSimulator:
    def __init__(self, agent_name: str = "english"):
        self.agent_name = agent_name
        self.voice_engine = NeuralVoiceEngine(default_agent=agent_name)
        self.extractor = QualificationExtractor()
        self.deflector = HallucinationDeflector()
        self.dialogue_history = []
        self.temp_dir = tempfile.mkdtemp(prefix="closer_sim_")

    def generate_agent_response(self, customer_utterance: str) -> str:
        """Determines the appropriate agent conversational turn with human sales guardrails."""
        lower = customer_utterance.lower()

        # Check for price deflection trigger
        is_price_query = any(k in lower for k in [
            "discount", "price", "rate", "cost", "offer", "lowest", "how much", "bargain", "discounts",
            "डिस्काउंट", "रेट", "कीमत", "कम", "ऑफर", "सस्ता", "छूट",
            "விலை", "தள்ளுபடி", "கம்மி", "டிஸ்கவுண்ட்", "ரேட்", "ஆஃபர்", "குறைக்க", "பர்சன்ட்"
        ])
        
        lang = str(VOICE_PROFILES[self.agent_name]["language"])

        # 1. Price Negotiation Deflection
        if is_price_query:
            if "Tamil" in lang:
                return "Sir, pricing மற்றும் special discount பத்தி நம்ம நேரடியா site visit வரும்போது பேசிக்கலாமுங்க. இந்த வியாழக்கிழமை சாயங்காலம் 4 மணிக்கு பார்க்கலாமா, இல்ல சனிக்கிழமை காலைல பார்க்கலாமா Sir?"
            elif "Hindi" in lang:
                return "हाँजी बिल्कुल! डिस्काउंट और final pricing के बारे में हम site visit पर बैठकर आराम से बात कर सकते हैं जी। क्या गुरुवार शाम 4 बजे या शनिवार सुबह का समय सही रहेगा सर?"
            else:
                return "Look, I totally get where you are coming from on the pricing. ... The developer actually authorizes custom payment milestones during the private walkthrough. Would Thursday at 4 PM or Saturday morning work better for you?"

        # Extract qualification
        dossier = self.extractor.extract(customer_utterance)
        
        # 2. Budget Qualification
        if dossier.budget_bracket:
            if "Tamil" in lang:
                return "கண்டிப்பா Sir! உங்க budget-க்கு ஏத்த மாதிரி OMR-ல ரொம்பவே அழகான 3 BHK luxury projects இருக்குங்க. இந்த weekend நேர்ல வந்து site visit பார்க்கலாமா Sir?"
            elif "Hindi" in lang:
                return "जी बिल्कुल सर! अगर आपका budget डेढ़ करोड़ के आस-पास है, तो हमारे पास बहुत ही शानदार 3 BHK luxury options हैं। क्या इस weekend एक बार site visit plan करें?"
            else:
                return "Got it, that fits our premium inventory perfectly. Would you like to schedule a private walkthrough this weekend?"

        # 3. Investor vs End-User
        if any(w in lower for w in ["invest", "investment", "end user", "personal", "stay", "வாடகை", "முதலீடு", "निवेश"]):
            if "Tamil" in lang:
                return "ரொம்ப நல்ல choice Sir! High rental yield தரக்கூடிய சூப்பரான investment options எங்ககிட்ட இருக்குங்க. இந்த சனிக்கிழமை நேர்ல வந்து பார்க்கலாமா Sir?"
            elif "Hindi" in lang:
                return "शानदार सर! हमारे पास high return देने वाले बहुत ही बेहतरीन investment options हैं जी। क्या मैं आपके लिए कल का slot confirm करूँ?"
            else:
                return "Understood. We have strong high-yield options. Would you prefer a morning or afternoon walkthrough?"

        # 4. Default opening
        if "Tamil" in lang:
            return "வணக்கம் Sir! நீங்க ஃபேமிலியோட stay பண்ண 3 BHK பாக்குறீங்களா, இல்ல investment-க்காக பாக்குறீங்களா Sir?"
        elif "Hindi" in lang:
            return "नमस्ते सर! आप अपने परिवार के साथ रहने के लिए 3 BHK फ्लैट देख रहे हैं या फिर investment के लिए?"
        else:
            return "Hey, good morning! ... Thanks for checking out our residences. Quick question — are you looking for a two-bedroom or a three-bedroom layout for your family?"

    async def speak_text(self, text: str) -> None:
        """Synthesizes text and plays it out loud on Mac speakers."""
        audio_file = os.path.join(self.temp_dir, f"turn_{int(time.time()*1000)}.wav")
        actual_path = await self.voice_engine.synthesize_to_file(text, audio_file, agent=self.agent_name)
        
        try:
            subprocess.run(["afplay", actual_path], check=True)
        except Exception:
            pass

    async def run_turn(self, customer_utterance: str) -> None:
        """Runs one full customer turn."""
        print(f"\n[You (Customer)]: \"{customer_utterance}\"")
        self.dialogue_history.append(f"Customer: {customer_utterance}")

        full_text = " ".join(self.dialogue_history)
        dossier = self.extractor.extract(full_text)

        start_t = time.time()
        agent_reply = self.generate_agent_response(customer_utterance)
        self.dialogue_history.append(f"Agent: {agent_reply}")
        latency_ms = (time.time() - start_t) * 1000

        profile = VOICE_PROFILES[self.agent_name]
        print(f"[{profile['label']}]: \"{agent_reply}\"")
        print(f"   ↳ [Latency: {latency_ms:.1f}ms | Words: {len(agent_reply.split())} | Ends with question: {agent_reply.endswith('?')}]")

        budget_str = f"{dossier.budget_bracket.currency} {dossier.budget_bracket.min_value} - {dossier.budget_bracket.max_value} {dossier.budget_bracket.unit}" if dossier.budget_bracket else "None yet"
        print(f"   ↳ [Live Dossier] Budget: {budget_str} | Persona: {dossier.buyer_type.value if dossier.buyer_type else 'Unstated'} | Review Flag: {dossier.requires_human_review}")

        print("   🔊 Speaking response through Mac speakers...")
        await self.speak_text(agent_reply)


async def run_automated_demo(agent_name: str = "english"):
    """Runs an automated conversation demonstration."""
    print(f"\n--- RUNNING HIGH-NATURALNESS AUDIO DEMO: {agent_name} ---")
    sim = CustomerTestingSimulator(agent_name=agent_name)
    
    if agent_name in ["tamil", "pallavi"]:
        opening = "வணக்கம் சார்! நீங்க family-யோட குடிவர 3BHK பாக்குறீங்களா, இல்ல investment-க்காகவா சார்?"
        t1 = "எனக்கு OMR-ல 1.5 Crores budget-ல 3BHK வேணும்."
        t2 = "Full cash payment பண்ணா 15% discount கிடைக்குமா?"
    elif agent_name in ["hindi", "swati"]:
        opening = "नमस्ते जी! आप अपने रहने के लिए 3BHK फ्लैट देख रहे हैं या फिर investment के लिए?"
        t1 = "मुझे 1.5 Crores के budget में 3BHK फ्लैट चाहिए।"
        t2 = "अगर मैं तुरंत book करूँ तो क्या 15% discount मिलेगा?"
    else:
        opening = "Hey, good morning! ... Thanks for checking out our residences. Quick question — are you looking for a two-bedroom or a three-bedroom layout for your family?"
        t1 = "Hi, I am looking for a 3BHK for my family with a budget of around 1.5 Crores."
        t2 = "Can I get a 15 percent cash discount if I book the unit this week?"

    print(f"\nAgent Opening: \"{opening}\"")
    await sim.speak_text(opening)

    for turn in [t1, t2]:
        await asyncio.sleep(0.5)
        await sim.run_turn(turn)


async def main():
    parser = argparse.ArgumentParser(description="CLOSER AI Live Customer Testing Sandbox")
    parser.add_argument("--demo", action="store_true", help="Run automated voice demonstration")
    parser.add_argument("--voice", type=str, default=None, help="Specify language: english, tamil, hindi")
    args = parser.parse_args()

    if args.demo:
        v = args.voice or "english"
        await run_automated_demo(v)
        return

    print("=" * 80)
    print("   CLOSER AI — HIGH-FIDELITY TRI-LINGUAL VOICE SANDBOX")
    print("   One Dedicated Premium Female Closer per Language (100% Free & Local)")
    print("=" * 80)
    print("Select Language / Closer:")
    print("  1. 🇺🇸 English: Signature CLOSER AI (Kokoro 3-Way SOTA Blend — Locked in)")
    print("  2. 🇮🇳 Tamil: பல்லவி (Pallavi — Tanglish Closer, Native TN Dialect)")
    print("  3. 🇮🇳 Hindi: स्वाति (Swati — Hinglish Closer, Real Telecaller Cadence)")
    print("-" * 80)

    choice = input("Enter choice (1-3) [Default: 1]: ").strip()
    agent_map = {
        "1": "english",
        "2": "tamil",
        "3": "hindi",
    }
    agent_key = agent_map.get(choice, "english")

    sim = CustomerTestingSimulator(agent_name=agent_key)
    profile = VOICE_PROFILES[agent_key]
    print(f"\n[✓] Connected to: {profile['label']}")
    print("Starting call... (Agent speaks opening greeting)\n")

    if agent_key == "tamil":
        opening = "வணக்கம் சார்! நீங்க family-யோட குடிவர 3BHK பாக்குறீங்களா, இல்ல investment-க்காகவா சார்?"
    elif agent_key == "hindi":
        opening = "नमस्ते जी! आप अपने रहने के लिए 3BHK फ्लैट देख रहे हैं या फिर investment के लिए?"
    else:
        opening = "Hey, good morning! ... Thanks for checking out our residences. Quick question — are you looking for a two-bedroom or a three-bedroom layout for your family?"

    print(f"[{profile['label']}]: \"{opening}\"")
    await sim.speak_text(opening)

    print("\n" + "=" * 80)
    print("   YOU ARE NOW THE CUSTOMER! Test the agent by typing your responses.")
    print("   Try: Haggling on price, stating budgets in Crores/Lakhs, asking about site visits.")
    print("   Type 'exit' or 'hangup' to end the call.")
    print("=" * 80)

    while True:
        try:
            user_input = input("\nYou (Customer) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "hangup"]:
                print("\n[Call Ended by Customer]")
                break
            await sim.run_turn(user_input)
        except (KeyboardInterrupt, EOFError):
            print("\n[Session Aborted]")
            break


if __name__ == "__main__":
    asyncio.run(main())
