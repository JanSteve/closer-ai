"""
Clinical Safety & DPDP Act 2023 Guardrails for Amura Health / CLOSER AI.
Enforces:
- Immediate 108 / Emergency Room escalation on red-flag symptoms (EN/TA/HI)
- Strict non-diagnostic & non-prescribing refusals routing to licensed physicians
- Explicit DPDP consent lifecycle + Section 7(f) medical-emergency exemption
- Prompt-injection blocking and PII masking for logs
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class SafetyDecision:
    allowed: bool
    emergency_108: bool
    category: str  # "emergency_108" | "no_diagnosis" | "no_prescribing" | "consent_required" | "prompt_injection" | "safe"
    action: str  # "escalate_108" | "refuse_clinical_advice" | "request_consent" | "block" | "allow"
    override_reply: Optional[str]
    dpdp_emergency_exemption: bool
    red_flags: List[str] = field(default_factory=list)


_EMERGENCY_PATTERNS: List[Tuple[str, str]] = [
    # Chest pain / cardiac
    (r"\b(chest\s*pain|chest\s*tightness|crushing\s*chest|heart\s*attack|radiating\s*(?:to\s*)?(?:my\s*)?(?:left\s*)?(?:arm|jaw))\b", "chest_pain_cardiac"),
    (r"(நெஞ்சு\s*வலி|நெஞ்சுவலி|நெஞ்சு\s*அடைப்பு|இதய\s*வலி|இடது\s*கை\s*வலி)", "chest_pain_ta"),
    (r"\b(nenju\s*vali|nenju\s*adaippu|idhu\s*heart\s*attack)\b", "chest_pain_tanglish"),
    (r"(सीने\s*में\s*(?:तेज\s*|भयंकर\s*)?दर्द|सीने\s*में\s*जकड़न|दिल\s*का\s*दौरा|बांह\s*में\s*खिंचाव)", "chest_pain_hi"),
    (r"\b(seene\s*mein\s*dard|chhati\s*mein\s*dard|dil\s*ka\s*daura)\b", "chest_pain_hinglish"),
    # Severe breathing distress
    (r"\b(severe\s*shortness\s*of\s*breath|shortness\s*of\s*breath|can'?t\s*(?:catch\s*my\s*)?breath|can'?t\s*breathe|cannot\s*breathe|difficulty\s*breathing|gasping\s*for\s*air)\b", "breathing_distress"),
    (r"(மூச்சு\s*விட\s*முடியல|மூச்சு\s*திணறல்|மூச்சுத்\s*திணறல்)", "breathing_distress_ta"),
    (r"\b(moochu\s*vida\s*mudiyala|moochu\s*thinaral)\b", "breathing_distress_tanglish"),
    (r"(सांस\s*लेने\s*में\s*(?:बहुत\s*)?तकलीफ|सांस\s*नहीं\s*आ\s*रही|दम\s*घुट\s*रहा)", "breathing_distress_hi"),
    (r"\b(saans\s*lene\s*mein\s*takleef|saans\s*nahi\s*aa\s*rahi|dam\s*ghut)\b", "breathing_distress_hinglish"),
    # Stroke signs
    (r"\b(slurred\s*speech|facial\s*droop|face\s*drooping|sudden\s*weakness|one\s*side\s*(?:weak|numb)|paralysis|stroke\s*signs?)\b", "stroke_neuro_signs"),
    (r"(பக்கவாதம்|முகம்\s*கோணுது|பேச்சு\s*குழறுது)", "stroke_ta"),
    (r"(लकवा|मुंह\s*टेढ़ा|बोलने\s*में\s*लड़खड़ाहट)", "stroke_hi"),
    # Severe bleeding / unconsciousness / seizures
    (r"\b(severe\s*bleeding|uncontrolled\s*bleeding|heavy\s*bleeding|fainted|unconscious|unresponsive|passed\s*out|seizure|convulsion)\b", "bleeding_unconscious_seizure"),
    (r"(அதிக\s*ரத்தப்போக்கு|மயக்கம்\s*போட்டு|சுயநினைவு\s*இல்லை|வலிப்பு)", "bleeding_unconscious_ta"),
    (r"(तेज\s*खून\s*बह|बेहोश|होश\s*नहीं|दौरा\s*पड़)", "bleeding_unconscious_hi"),
    # Self-harm / suicidal ideation
    (r"\b(end\s*my\s*life|kill\s*myself|suicid(?:e|al)|self[-\s]?harm|want\s*to\s*die)\b", "self_harm_crisis"),
    (r"(தற்கொலை|சாகணும்\s*போல|உயிரை\s*மாய்த்து)", "self_harm_ta"),
    (r"(आत्महत्या|खुद\s*को\s*नुकसान|जान\s*देना\s*चाहता)", "self_harm_hi"),
]

_INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?(?:previous|prior|above)\s+instructions",
    r"(reveal|output|print|show|repeat|dump)\s+(your\s+)?(system\s+prompt|hidden\s+instructions|rules|instructions\s+above)",
    r"bypass\s+(safety|guardrails|clinical\s+rules|restrictions)",
    r"\b(jailbreak|dan\s+mode|developer\s+mode|god\s+mode|unrestricted\s+mode)\b",
    r"(pretend|act\s+as|roleplay)\s+(?:you\s+are|like)\s+(?:a\s+doctor|an?\s+unrestricted|someone\s+with\s+no\s+rules)",
    r"(hypothetical(?:ly)?|for\s+(?:educational|research|fiction)\s+purposes?).*(prescribe|diagnose|hack|bypass|api\s*key)",
    r"\b(forget\s+your\s+rules|override\s+clinical\s+safety|disregard\s+guidelines)\b",
]

_CONFIDENTIAL_PATTERNS: List[str] = [
    r"\b(api[\s_-]?key|secret[\s_-]?key|env\s+var|\.env|password|credentials|database\s+schema|sqlite|source\s+code|backend\s+code)\b",
    r"\b(other\s+patients?|patient\s+list|patient\s+database|someone\s+else'?s\s+(?:report|record|phone|data))\b",
    r"\b((?:doctor|dr\.?|physician|founder|ceo|saravanan|godwin|his|her)(?:\s+[a-z]+)?'?s?\s+(?:personal|private|home|direct)\s+(?:phone|number|mobile|cell|whatsapp|address|email)|(?:dr\.?|doctor|godwin|saravanan)(?:\s+[a-z]+)?'?s?\s+(?:whatsapp|cell|mobile)\b|internal\s+margin|revenue\s+data)\b",
    r"(மற்ற\s+நோயாளி|டாக்டர்\s+பர்சனல்\s+நம்பர்|பாஸ்வேர்ட்|சீக்ரெட்)",
    r"(दूसरे\s+मरीज़|डॉक्टर\s+का\s+पर्सनल\s+नंबर|पासवर्ड|सीक्रेट|डेटाबेस)",
]

_OFFTOPIC_RESTRICTED_PATTERNS: List[str] = [
    r"\b(hack\s+into|exploit|sql\s+injection|phishing|malware|ransomware|build\s+a\s+bomb|weapon|illegal\s+drugs?)\b",
    r"\b(write\s+python\s+code|crypto\s+signals?|stock\s+tips?|betting|gambling)\b",
]

_PRESCRIBING_PATTERNS: List[str] = [
    r"\b(prescribe|prescription|write\s+a\s+rx|which\s+(?:medicine|tablet|drug|pill)|what\s+(?:medicine|tablet|drug|dose|dosage)\s+should\s+i\s+take)\b",
    r"\b(increase|decrease|reduce|double|stop|start|adjust|change)\s+(?:my\s+)?(insulin|metformin|glimepiride|thyroid|levothyroxine|thyronorm|bp\s*tablet|medication|medicine|dose|dosage)\b",
    r"\b(how\s+many\s+units\s+of\s+insulin|how\s+much\s+(?:metformin|insulin|mg)\s+(?:should\s+i|to)\s+take|should\s+i\s+take\s+\d+\s*mg)\b",
    r"(என்ன\s*மாத்திரை|டோஸ்\s*அதிகம்|இன்சுலின்\s*அளவு|மருந்து\s*எழுதி|மாத்திரை\s*சாப்பிடணும்)",
    r"\b(enna\s*tablet\s*saapdanum|dose\s*solla|insulin\s*dose\s*maathalama|tablet\s*stop\s*pannalama)\b",
    r"(कौन\s*सी\s*दवाई|कितनी\s*डोज़|दवाई\s*बताइए|इंसुलिन\s*बढ़ा|मेडिसिन\s*लिख|गोली\s*कम\s*कर)",
    r"\b(kaun\s*si\s*dawai|kitni\s*dose|insulin\s*badhaun|dawai\s*likh\s*do)\b",
]

_DIAGNOSIS_PATTERNS: List[str] = [
    r"\b(diagnose\s*me|give\s+me\s+a\s+diagnosis|what\s+disease\s+do\s+i\s+have|do\s+these\s+(?:lab\s+values|reports?|symptoms?)\s+mean\s+i\s+have|do\s+i\s+have\s+(?:diabetes|fatty\s+liver|pcos|pcod|thyroid|cancer|heart\s+disease)|confirm\s+if\s+i\s+have|tell\s+me\s+what\s+condition\s+i\s+have)\b",
    r"(எனக்கு\s*(?:சுகர்|சர்க்கரை|நோய்)\s*இருக்கா|ரிப்போர்ட்\s*பார்த்து\s*நோய்\s*சொல்லுங்க)",
    r"\b(enakku\s*(?:sugar|diabetes|thyroid|pcos)\s*irukka(?:\s*illaya)?(?:\s*sollunga)?|report\s*paathu\s*diagnose)\b",
    r"(रिपोर्ट\s*देखकर\s*बताइए|मुझे\s*कौन\s*सी\s*बीमारी\s*है|क्या\s*मुझे\s*(?:डायबिटीज|शुगर|थायरॉइड|बीमारी)\s*है|डायग्नोज़)",
    r"\b(report\s*dekh\s*kar\s*bataiye|mujhe\s*kaun\s*si\s*bimari\s*hai|kya\s*mujhe\s*diabetes\s*hai)\b",
]


class ClinicalSafetyGuardrails:
    """
    Deterministic clinical safety and DPDP Act 2023 compliance gate.
    Runs before LLM reasoning on every patient turn.
    """

    def __init__(self, initial_consent: str = "pending") -> None:
        self.consent_status: str = initial_consent

    @staticmethod
    def _normalize_lang(language: str) -> str:
        low = (language or "english").lower().strip()
        if any(k in low for k in ("tamil", "ta")):
            return "tamil"
        if any(k in low for k in ("hindi", "hi")):
            return "hindi"
        return "english"

    def update_consent(self, text: str = "", explicit_flag: Optional[bool] = None) -> str:
        """Tracks explicit DPDP Act 2023 patient consent state."""
        if explicit_flag is True:
            self.consent_status = "granted"
            return self.consent_status
        if explicit_flag is False:
            self.consent_status = "declined"
            return self.consent_status

        t = (text or "").lower().strip()
        if not t:
            return self.consent_status

        if re.search(
            r"\b(do\s+not\s+consent|don'?t\s+consent|no\s+consent|decline\s+consent|not\s+consent|don'?t\s+record|no\s+whatsapp\s+follow-?up|opt\s*out)\b"
            r"|(சம்மதம்\s*இல்லை|ரெக்கார்ட்\s*வேண்டாம்|सहमति\s*नहीं|रिकॉर्ड\s*मत)",
            t,
            re.IGNORECASE,
        ):
            self.consent_status = "declined"
        elif re.search(
            r"\b(i\s+consent|yes[, ]+i\s+consent|consent\s+granted|i\s+agree\s+to\s+share|you\s+may\s+record|okay\s+to\s+share)\b"
            r"|(சம்மதம்|சரிங்க,?\s*சம்மதம்|हाँ,?\s*मैं\s*सहमत\s*हूँ|सहमति\s*है)",
            t,
            re.IGNORECASE,
        ):
            self.consent_status = "granted"
        return self.consent_status

    def mask_pii(self, text: str) -> str:
        """Redacts Aadhaar, PAN, phone numbers, and emails before logging or analytics."""
        if not text:
            return ""
        masked = text
        # Email
        masked = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[MASKED_EMAIL]", masked)
        # PAN (Indian 10-char alphanumeric)
        masked = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[MASKED_PAN]", masked)
        # Aadhaar (12 digits with optional spaces/hyphens)
        masked = re.sub(
            r"\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b",
            r"**** **** \3",
            masked,
        )
        # Phone numbers (+91 / +1 / 10-digit Indian mobile)
        masked = re.sub(
            r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){10}(?!\d)",
            "[MASKED_PHONE]",
            masked,
        )
        return masked

    def evaluate(
        self,
        text: str,
        language: str = "english",
        consent_granted: Optional[bool] = None,
    ) -> SafetyDecision:
        """Evaluates patient utterance for 108 emergencies, prompt injection, diagnosis, and prescribing."""
        self.update_consent(text, explicit_flag=consent_granted)
        lang = self._normalize_lang(language)
        t_low = (text or "").lower().strip()

        # 1. Immediate Emergency 108 / ER check (DPDP Section 7(f) overrides consent blocks)
        red_flags: List[str] = []
        for pattern, flag_name in _EMERGENCY_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                red_flags.append(flag_name)

        if red_flags:
            self.consent_status = "emergency_exempt_section_7f"
            if lang == "tamil":
                msg = (
                    "தயவுசெய்து உடனே 108 அவசர உதவி எண்ணை அழைக்கவும் அல்லது அருகிலுள்ள அவசர சிகிச்சைப் பிரிவுக்கு (ER) செல்லவும். "
                    "இது உடனடி மருத்துவ உதவி தேவைப்படும் அறிகுறியாக இருக்கலாம்; தொலைபேசி வழியே மருத்துவ ஆலோசனை வழங்க முடியாது. "
                    "நீங்கள் அருகில் உள்ள மருத்துவமனைக்குச் செல்ல உதவ உங்கள் குடும்பத்தினரையும் உடனே அழைக்கவும்."
                )
            elif lang == "hindi":
                msg = (
                    "कृपया तुरंत 108 इमरजेंसी एम्बुलेंस पर कॉल करें या नजदीकी अस्पताल के इमरजेंसी रूम (ER) में जाएँ। "
                    "ये लक्षण तुरंत डॉक्टर की प्रत्यक्ष जांच की मांग करते हैं और मैं फोन पर आपातकालीन चिकित्सा सलाह नहीं दे सकती। "
                    "कृपया बिना देर किए 108 पर संपर्क करें।"
                )
            else:
                msg = (
                    "Please call 108 emergency services immediately or go to the nearest hospital Emergency Room (ER) right away. "
                    "These symptoms require urgent in-person medical evaluation, and an automated voice assistant cannot assess emergencies. "
                    "Under DPDP Section 7(f) medical emergency exemption, please prioritize calling 108 now."
                )
            return SafetyDecision(
                allowed=False,
                emergency_108=True,
                category="emergency_108",
                action="escalate_108",
                override_reply=msg,
                dpdp_emergency_exemption=True,
                red_flags=red_flags,
            )

        # 2. Prompt Injection / Jailbreak blocking
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                if lang == "tamil":
                    inj_msg = (
                        "நான் Amura Health மருத்துவ ஆலோசனை ஒருங்கிணைப்பாளர். "
                        "பாதுகாப்பு விதிகளை மீறவோ, உள் விவரங்களைப் பகிரவோ, மருந்து பரிந்துரைக்கவோ முடியாது. "
                        "உங்கள் மருத்துவர் ஆலோசனையை முன்பதிவு செய்ய உதவட்டுமா?"
                    )
                elif lang == "hindi":
                    inj_msg = (
                        "मैं Amura Health की क्लिनिकल केयर कोऑर्डिनेटर हूँ। "
                        "मैं सुरक्षा नियम नहीं तोड़ सकती और न ही कोई दवा या निदान बता सकती हूँ। "
                        "क्या मैं आपका डॉक्टर कंसल्टेशन बुक करूँ?"
                    )
                else:
                    inj_msg = (
                        "I am Amura Health's clinical front-desk coordinator. "
                        "I cannot override clinical safety guardrails, roleplay past restrictions, reveal internal instructions, or issue medical diagnoses or prescriptions. "
                        "How can I help you schedule a physician consultation?"
                    )
                return SafetyDecision(
                    allowed=False,
                    emergency_108=False,
                    category="prompt_injection",
                    action="block",
                    override_reply=inj_msg,
                    dpdp_emergency_exemption=False,
                    red_flags=[],
                )

        # 2b. Confidential / PHI / Internal Infrastructure Protection
        for pattern in _CONFIDENTIAL_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                if lang == "tamil":
                    c_msg = "மன்னிக்கவும், நோயாளிகளின் தனிப்பட்ட தகவல்கள், மருத்துவர்களின் தனிப்பட்ட எண்கள் அல்லது நிறுவனத்தின் ரகசியத் தகவல்களைப் பகிர முடியாது. உங்கள் மருத்துவ ஆலோசனைக்கு உதவட்டுமா?"
                elif lang == "hindi":
                    c_msg = "क्षमा करें, मैं अन्य मरीज़ों का डेटा, डॉक्टरों के पर्सनल नंबर या सिस्टम से जुड़ी गोपनीय जानकारी साझा नहीं कर सकती। क्या मैं आपकी डॉक्टर कंसल्टेशन में मदद करूँ?"
                else:
                    c_msg = (
                        "I cannot share confidential internal details, system credentials, doctor personal contacts, or other patients' health records under DPDP privacy policy. "
                        "I'm happy to help with your own appointment or Amura Health care inquiries."
                    )
                return SafetyDecision(
                    allowed=False,
                    emergency_108=False,
                    category="confidential_blocked",
                    action="block",
                    override_reply=c_msg,
                    dpdp_emergency_exemption=False,
                    red_flags=[],
                )

        # 2c. Illegal / Off-topic Restriction
        for pattern in _OFFTOPIC_RESTRICTED_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                return SafetyDecision(
                    allowed=False,
                    emergency_108=False,
                    category="off_topic_restricted",
                    action="block",
                    override_reply=(
                        "I am strictly scoped to legal, clinically appropriate Amura Health patient care, OPD scheduling, and metabolic program support. "
                        "How can I assist with your health consultation today?"
                    ),
                    dpdp_emergency_exemption=False,
                    red_flags=[],
                )

        # 3. No Prescribing / Medication Dosage Adjustment
        for pattern in _PRESCRIBING_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                if lang == "tamil":
                    msg = (
                        "மன்னிக்கவும், நான் மருந்துகளையோ இன்சுலின்/மாத்திரை அளவுகளையோ பரிந்துரைக்கவோ மாற்றவோ முடியாது. "
                        "உங்கள் மருத்துவரின் ஆலோசனை இல்லாமல் மருந்தை மாற்ற வேண்டாம். "
                        "Amura Health-ன் பதிவு பெற்ற மருத்துவருடன் (physician) உடனடி ஆலோசனை நேரம் பதிவு செய்யட்டுமா?"
                    )
                elif lang == "hindi":
                    msg = (
                        "क्षमा करें, मैं कोई भी दवाई या इंसुलिन/टैबलेट की डोज़ नहीं लिख सकती और न ही बदलने की सलाह दे सकती हूँ। "
                        "कृपया डॉक्टर की सलाह के बिना अपनी दवाई न बदलें। "
                        "क्या मैं Amura Health के लाइसेंस प्राप्त डॉक्टर के साथ आपका कंसल्टेशन बुक कर दूँ?"
                    )
                else:
                    msg = (
                        "I cannot prescribe medications or advise changing your insulin or tablet dosage. "
                        "Please do not alter any prescribed medication without speaking directly to a doctor. "
                        "Would you like me to schedule a consultation with a licensed Amura Health physician to review your treatment safely?"
                    )
                return SafetyDecision(
                    allowed=False,
                    emergency_108=False,
                    category="no_prescribing",
                    action="refuse_clinical_advice",
                    override_reply=msg,
                    dpdp_emergency_exemption=False,
                    red_flags=[],
                )

        # 4. No Diagnosing from Symptoms / Reports
        for pattern in _DIAGNOSIS_PATTERNS:
            if re.search(pattern, t_low, re.IGNORECASE):
                if lang == "tamil":
                    msg = (
                        "மன்னிக்கவும், அறிகுறிகள் அல்லது லேப் ரிப்போர்ட்டை வைத்து நோயை உறுதிப்படுத்தும் (diagnose) உரிமை எனக்கு இல்லை. "
                        "Amura Health-ன் மருத்துவர் உங்கள் ரிப்போர்ட்டை முழுமையாகப் பார்த்து சரியான வழிகாட்டுதல் வழங்குவார். "
                        "உங்கள் பெயரும் வசதியான நேரமும் சொன்னால் டாக்டர் கன்சல்டேஷன் புக் செய்து தருகிறேன்."
                    )
                elif lang == "hindi":
                    msg = (
                        "क्षमा करें, मैं आपके लक्षणों या लैब रिपोर्ट के आधार पर किसी बीमारी का निदान (diagnosis) नहीं कर सकती। "
                        "Amura Health के अनुभवी डॉक्टर आपकी रिपोर्ट की समीक्षा करके सही चिकित्सकीय सलाह देंगे। "
                        "क्या मैं आज या कल के लिए डॉक्टर कंसल्टेशन स्लॉट बुक कर दूँ?"
                    )
                else:
                    msg = (
                        "I cannot diagnose medical conditions or interpret lab reports to confirm a disease. "
                        "A licensed Amura Health physician will review your biomarkers and medical history during a clinical consultation. "
                        "Would you like me to help book an online or Velachery clinic consultation?"
                    )
                return SafetyDecision(
                    allowed=False,
                    emergency_108=False,
                    category="no_diagnosis",
                    action="refuse_clinical_advice",
                    override_reply=msg,
                    dpdp_emergency_exemption=False,
                    red_flags=[],
                )

        return SafetyDecision(
            allowed=True,
            emergency_108=False,
            category="safe",
            action="allow",
            override_reply=None,
            dpdp_emergency_exemption=False,
            red_flags=[],
        )
