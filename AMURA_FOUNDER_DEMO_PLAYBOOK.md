# CLOSER AI × Amura Health — Founder Meeting & Live Demo Playbook

**Target Company:** Amura Health (`amura.ai`), 11th Floor, One National Park, 142 Velachery Main Road, Chennai 600042  
**Founders:** Saravanan Balakrishnan (Founder & CEO), Dr. Godwin Samuel Christudas (Co-founder & CMO), Yashwant Saravanan (Co-founder)  
**Your Goal:** Show a working, emotion-aware, clinically safe AI Voice Concierge that plugs straight into Amura's patient onboarding, metabolic care follow-ups, and hospital OPD triage—so they see your execution power on the spot.

---

## 1. Why Amura Needs This (Based on Research)
- Amura is **not a traditional bed-and-surgery hospital**; it is a high-touch **digital metabolic & chronic-care clinic** (Type-2 Diabetes, PCOD, Thyroid, Autoimmune, gut health via Medical Nutrition & Natural Molecule Therapy).
- Public client feedback highlights two big operational bottlenecks:
  1. **Response delays** when patients have questions or want updates between doctor/coach check-ins.
  2. **Coach rotation & drop-off** during strict dietary protocols.
- **How CLOSER AI solves this:** Instant `<120ms` callbacks when a patient submits an inquiry on `amura.ai`, daily adherence check-ins in **English, Chennai Tamil, or Hindi**, automatic booking onto physician calendars, and WhatsApp fasting lab checklists—all without sounding like a robotic IVR.

---

## 2. How It Gets Its Own Phone Number & Calls Real People

### How to Get a Dedicated Clinic Phone Number (India + Global)
1. **Indian Virtual Number (DID) via Exotel / Plivo / Twilio India:**
   - Cost: ~₹500–₹1,500/month for a dedicated Chennai `+91-44-...` or Pan-India `+91-...` number.
   - **TRAI DLT Registration:** Register Amura Health as a Principal Entity (PE) on Jio/Airtel/Vodafone DLT and link the telemarketer ID. Call **only opt-in patients** (people who submitted a consultation form or signed up for care reminders).
2. **Connecting the Number to CLOSER AI:**
   - Point the carrier's **SIP Trunk / Webhook** to **LiveKit SIP (`src/closer/integrations/livekit_sip.py`)** or **Bland AI (`closer/telephony/bland_engine.py`)**.
   - Set `BLAND_API_KEY` (or `LIVEKIT_URL` + `EXOTEL_SID` / `TWILIO_ACCOUNT_SID`) and `CLINIC_DID_NUMBER` in `.env`.
3. **How to Trigger a Live Demo Call During the Meeting:**
   - Open **`https://closer-ai-tawny.vercel.app/`** → click **Live Demo** (`#demoModal`).
   - Scroll to **`// LIVE OUTBOUND DEMO CALL (CLINIC DID)`**, enter the founder's mobile number (e.g. `+91 98400 XXXXX`), and click **`Place Demo Call`**.
   - If carrier keys (`BLAND_API_KEY` / LiveKit SIP) are present in `.env`, it rings their actual handset via `POST /api/call/demo`. Without carrier keys on a fresh laptop, it validates the number, DPDP consent, and DLT pipeline cleanly in Demo Mode while you run the live voice conversation right in the browser!

---

## 3. Healthcare & Telecom Complications to Be Careful About
Mentioning these proactively shows the founder you build **production-safe healthcare AI**, not toy wrappers:

1. **Zero Medical Diagnosis / Zero Prescribing (`src/closer/agent/clinical_guardrails.py`):**
   - If a patient asks *"What tablet should I take?"* or *"How many units of insulin should I increase?"*, CLOSER AI **strictly refuses** to prescribe or diagnose and routes them to a licensed Amura physician.
2. **Immediate 108 / Emergency Room Escalation:**
   - Any mention of **chest pain, shortness of breath, fainting, stroke signs, or severe bleeding** (in English, Tamil, or Hindi) immediately overrides normal booking and instructs the caller to dial **108** or visit the nearest ER.
3. **India DPDP Act 2023 & Call Recording Consent:**
   - Patient health details (HbA1c, meds, symptoms) are sensitive personal data. Outbound/inbound flows require explicit callback/recording consent (with Section 7(f) medical-emergency exception).
4. **TRAI DLT & Robocall Rules (India):**
   - Never blast cold numbers. Only dial opt-in web inquiries or existing patients with callback consent, using DLT-approved clinic headers.
5. **TTS Credit / Carrier Fallback Protection:**
   - If primary Indic TTS (e.g., Sarvam `bulbul:v3`) runs out of credits (`402`) or times out, CLOSER AI automatically cascades to **Studio Broadcast Neural / Edge TTS** and **Browser Speech Synthesis**—so a live call never freezes or outputs `"undefined"`.

---

## 4. How Emotion Understanding & Expressive Voice Work
Standard hospital IVRs say *"Press 1 for appointments"* in a flat robotic voice. CLOSER AI runs **`EmotionDetector` (`src/closer/agent/emotion.py`)** on every turn:
- **6 Detected States:** `pain_distress`, `urgent`, `anxious`, `frustrated`, `confused`, `calm` (across English, Tamil/Tanglish, and Hindi/Hinglish).
- **Real-Time Prosody Modulation:**
  - When a patient sounds **anxious** (e.g., *"I am really worried my HbA1c is 9.2"*), CLOSER AI slows speech rate (`-8%`), lowers pitch (`-2Hz`), switches to `empathetic` tone, reassures them warmly, and offers a physician slot.
  - When a patient sounds **frustrated** about a delayed callback, it switches to `warm_patient`, apologizes without defensiveness, and logs a priority support ticket (`#CC-84291`).

---

## 5. Exact 3-Minute Live Demo Script for the Founder Meeting
1. **Open the Landing Page (`https://closer-ai-tawny.vercel.app/`):**
   - Show the **#voice-studio** soundboard in **English (Maya)**, **Chennai Tamil (Priya)**, and **Hindi (Ritu)**.
   - Scroll to **#roi** and drag the sliders to Amura's monthly inquiry volume to show recovered consultations.
2. **Click `Live Demo` (`#demoModal`) and run these 3 live turns:**
   - **Turn 1 (Emotion + Safety):** Click or say *"I am really worried my HbA1c is 9.2, how much insulin should I take?"* → Point out `EMOTION: ANXIOUS (-8%)`, the warm reassuring voice, and the strict refusal to adjust insulin.
   - **Turn 2 (Emergency 108 Guardrail):** Say *"I have severe chest pain and cannot breathe."* → Point out the instant `108 EMERGENCY` override.
   - **Turn 3 (Chennai Tamil + Booking):** Switch to **தமிழ் (Priya)** and click *"நாளை காலை 11:30 மணிக்கு doctor consultation புக் பண்ண முடியுமா?"* → Show the live **Clinical Intake Dossier** updating + WhatsApp lab checklist dispatch.
3. **Ask for "The Missing Piece":**
   - *"This is running end-to-end today. What is the one EHR/CRM webhook and clinical intake protocol Amura uses internally so I can wire this into your live Velachery workflow this week?"*
