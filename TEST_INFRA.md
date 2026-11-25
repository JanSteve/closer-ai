# CLOSER AI Automated Video Generation & Scheduled Publishing Pipeline
# E2E Test Infrastructure Specification (TEST_INFRA.md)

## 1. Test Philosophy & Principles

The CLOSER AI E2E Testing Track establishes a comprehensive, requirement-driven verification framework for the automated video generation, peak Indian market scheduling, queue management, and automated publishing pipeline.

### Core Testing Principles:
1. **Opaque-Box Requirement-Driven**:
   Tests treat the subsystem implementations as opaque units, validating observable inputs, outputs, side effects, and state transitions against the authoritative specifications defined in `ORIGINAL_REQUEST.md` and `PROJECT.md`.
2. **Deterministic & Self-Contained**:
   Tests run 100% locally with zero external network dependencies and zero production credentials. All external endpoints (Meta Instagram Graph API v21.0, Make.com Custom Webhook) are simulated via high-fidelity, thread-safe mock servers validating exact cryptographic signatures and payload structures.
3. **No Facade Tests**:
   Every test executes real logic, asserting strict schemas, mathematical boundary calculations (LUFS audio levels, pixel safe zones Y=1360 and Y=1530, aspect ratios, byte ranges), SQLite ACID guarantees, HMAC-SHA256 digests, and temporal assertions.
4. **Adversarial Verification**:
   The suite actively subjects the pipeline to boundary stresses: clock drift > 300s, signature tampering, missing media assets, extreme video durations, Meta API rate limits (50 posts/24h), and race conditions during concurrent worker dispatches.
5. **Zero-Flake Execution**:
   All tests run reliably within standard CI environments (GitHub Actions) with predictable execution times and binary exit code semantics (`0` for success, non-zero for any assertion failure).

---

## 2. Test Architecture & Runner Setup

### 2.1 Runner Location & Execution Command
- **Test Directory**: `tests/e2e/`
- **Execution Command**:
  ```bash
  pytest tests/e2e/ -v
  ```
- **Filter by Tier**:
  ```bash
  pytest tests/e2e/test_tier1_features.py -v
  pytest tests/e2e/test_tier2_boundaries.py -v
  pytest tests/e2e/test_tier3_combinations.py -v
  pytest tests/e2e/test_tier4_scenarios.py -v
  ```

### 2.2 Suite Layout
```
tests/e2e/
├── __init__.py
├── conftest.py                   # Pytest fixtures: Mock servers, SQLite DBs, temporary directories, sample payloads
├── test_tier1_features.py        # Tier 1: Happy-path feature verification (F1-F22)
├── test_tier2_boundaries.py      # Tier 2: Boundary conditions, rate limits, clock drift, corrupt inputs
├── test_tier3_combinations.py    # Tier 3: Cross-feature interactions and state transitions
└── test_tier4_scenarios.py       # Tier 4: 5 Real-world end-to-end industry application scenarios
```

### 2.3 Pass/Fail Semantics
- **Passing**:
  - All test assertions evaluate truthy.
  - Zero uncaught exceptions.
  - Exit code `0`.
- **Failing**:
  - Any failed assertion halts test execution with a descriptive failure message detailing expected vs actual.
  - Non-zero exit code (`1`).
  - Unhandled network calls (any un-mocked external request is intercepted and failed).

---

## 3. Feature Inventory & Tier Mapping (F1 to F22)

The 22 core features cataloged in `PROJECT.md` are mapped across four testing tiers:
- **Tier 1 (Happy-Path Features)**: Primary functional verification of each component in isolation and direct pipeline flow.
- **Tier 2 (Boundaries & Edge Cases)**: Edge conditions, invalid data, timeouts, clock drifts, extreme values.
- **Tier 3 (Cross-Feature Combinations)**: Multi-component interactions, state machine handoffs, atomic transactions.
- **Tier 4 (Real-World Scenarios)**: Complete end-to-end business workflows from sector script to published container.

| Feature ID | Feature Name | Milestone | Tier 1 (Happy Path) | Tier 2 (Boundaries & Corners) | Tier 3 (Cross-Feature Combinations) | Tier 4 (Real-World Scenarios) |
|:---|:---|:---:|:---|:---|:---|:---|
| **F1** | Sector Scenario Templates | M1 | 5 Sector presets generate valid scripts & visual cues | Empty/None fields, unsupported sector tags | Scenario manifest ingested into voice synthesizer | Clinic, Solar, Real Estate, EdTech, Agency scripts |
| **F2** | Dual Voice Synthesis Engine | M1 | Generates audio for English, Tamil, Hindi | Empty text, extreme text length (> 2000 chars) | Synthesized audio duration fed to turn sequencer | Multilingual voice generation for all 5 scenarios |
| **F3** | Dynamic Foley & Audio Mixer | M1 | Voice ducking at -8.5 dB, -14.0 LUFS limiter | Pure silence, clipped audio, zero-length tracks | Audio duration synchronization with Canvas 2D | Master audio mix rendered with voice ducking |
| **F4** | Vertical Canvas 2D Stage | M1 | 1080x1920 9:16 viewport, character rigs & attire | Canvas out-of-bounds coordinates, invalid fps | Frame render pacing synced with audio timestamps | Full 9:16 canvas scene rendering |
| **F5** | Safe-Zone Subtitle Renderer | M1 | Karaoke highlight, anchored strictly at Y = 1360 | Long subtitles wrapping beyond 680px width | Word-level timing synchronized with audio speech | Subtitles rendered in safe zone across all 5 reels |
| **F6** | Viral CTA Banner Hook | M1 | Safe-zone CTA prompt at Y = 1530: "Comment CLOSER" | Missing keyword, multi-line banner overflow | CTA metadata propagated to webhook and Instagram caption | CTA prompt verified in final payload and video |
| **F7** | Multi-Format FFmpeg Exporter | M1 | Export 1080p MP4, 720p, 1:1, MP3, SRT, poster JPG | Missing audio track, corrupt video stream | Multi-format manifest bundled with `daily_reel.json` | 6 asset formats generated for each scenario |
| **F8** | Programmatic Batch CLI | M1 | Batch generator CLI parses arguments and executes | Invalid CLI arguments, non-existent output paths | CLI outputs enqueued into SQLite database | Automated batch rendering of daily reels |
| **F9** | 14-Slot Indian Timetable | M2 | Exactly 14 slots across Monday–Sunday (2 slots/day) | Leap year, Sunday-to-Monday week wrap | Auto-slot assignment matching next due slot | Reels assigned to designated IST peak slots |
| **F10** | Dual-Layer Queue Database | M2 | SQLite table CRUD + synced JSON mirror | Disk write failure, invalid JSON mirror parse | SQLite transaction rollback on failure | Database holds queue states for all reels |
| **F11** | 7-State Lifecycle Machine | M2 | DRAFT ➔ RENDERED ➔ QUEUED ➔ SCHEDULED ➔ DISPATCHING ➔ PUBLISHED | Illegal transitions (e.g. DRAFT to PUBLISHED) | Atomic claim transitions with concurrent locks | Reels progress cleanly from DRAFT to PUBLISHED |
| **F12** | Premature Posting Guard | M2 | Slot time in past allows dispatch | Slot time 1 second in future rejects dispatch | Dual SQL + Python assertion gate verification | Prevents premature release of future-scheduled reels |
| **F13** | Queue Management CLI & API | M2 | CLI commands: queue, list, next-due, mark-dispatched | Queueing non-existent file paths raises error | CLI `next-due` feeds `dispatch_due_reels` | Queue inspection and status updates |
| **F14** | 48-Hour Buffer Manager | M2 | Buffer depth calculation (4–6 reels maintained) | Buffer starvation (< 2 reels) triggers alert | Low watermark triggers batch generator | Buffer health verified across multi-day cycle |
| **F15** | Instagram Graph API Client | M3 | Container creation, polling, publish lifecycle | Subcode 2207003, 2207053, 2207032 handling | Container ID stored in SQLite upon creation | Real-world simulated publishing with permalink |
| **F16** | Make.com Webhook Dispatcher | M3 | Webhook POST with full JSON schema and CTA hook | Malformed JSON payload, missing required keys | Webhook response triggers status update to PUBLISHED | Webhook dispatched with scenario metadata |
| **F17** | HMAC-SHA256 & Replay Guard | M3 | Valid `X-Closer-Signature` & timestamp accepted | Tampered signature, timestamp drift > 300s | Receiver rejects invalid signature before processing | Security headers validated for every dispatch |
| **F18** | GitHub Actions Dual Workflow | M3 | Workflow YAML schema validity (02:00 IST + `*/30`) | Missing environment secrets, runner failure | Dual cron trigger invokes batch + dispatch scripts | Workflow execution flow simulation |
| **F19** | Mock Instagram Graph API | M4 | Standalone HTTP server simulates Meta v21.0 | Simulates 50 posts/24h rate limit (subcode 2207042) | Mock server captures container states | Mock server receives requests in all tests |
| **F20** | Mock Make.com Webhook Server | M4 | Standalone HTTP server validates HMAC & returns 200 | Returns 403 on signature mismatch, 400 on drift | Mock server logs execution IDs for verification | Mock server handles all webhook dispatches |
| **F21** | Zero-Credential E2E Suite | M4 | Automated execution with exit code 0 | Non-zero exit on assertion failure | Full pipeline integration without network | Pytest runner executes cleanly |
| **F22** | Setup Guide & Env Config | M4 | Validates required `.env` keys and defaults | Missing critical keys triggers configuration error | Environment loads into client configurations | Complete configuration loaded across all tests |

---

## 4. Real-World Application Scenarios (Tier 4)

The Tier 4 test suite executes 5 complete real-world scenarios representing CLOSER AI's primary target Indian business sectors:

### Scenario 1: Clinic Emergency / Lead Drop-off
- **Industry & Language**: Healthcare & Aesthetic Clinics (Dental Implants, Hair Transplants), Tamil (`ta-IN-PallaviNeural`) & Indian English.
- **Problem**: Inbound leads generated on Meta ads after 9 PM go cold while surgeons are in daytime operations; reception calls 18 hours late, lead hangs up.
- **Scheduled Slot**: Tuesday Slot 1 — 13:15 IST (OPD Lunch Break).
- **CTA Hook**: "👇 COMMENT 'CLOSER' BELOW 👇 for our Dental & Hair Clinic Automated Lead Qualification Protocol."
- **WhatsApp Asset**: `VIP_Clinic_Consultation_Pass.pkpass`.
- **E2E Flow**: Script generation ➔ Audio synthesis ➔ Safe-zone verification (Y=1360) ➔ Tuesday 13:15 IST slot queueing ➔ Temporal gate verification ➔ Make.com webhook dispatch with HMAC ➔ Mock Instagram container publish ➔ Verification of `PUBLISHED` state and permalink.

### Scenario 2: Solar Subsidy Rush
- **Industry & Language**: Rooftop Solar & Clean Energy EPC, Hindi (`hi-IN-SwaraNeural`) & Indian English.
- **Problem**: Homeowners inquiring about ₹78,000 PM Surya Ghar rooftop solar subsidies wait 3 days for technical quotes and drop off.
- **Scheduled Slot**: Wednesday Slot 1 — 09:00 IST (Morning Field Push).
- **CTA Hook**: "👇 COMMENT 'CLOSER' BELOW 👇 for the PM Surya Ghar 5kW Subsidy Prompt & Calculator."
- **WhatsApp Asset**: `5kW_Solar_PM_Surya_Ghar_Quotation.pdf`.
- **E2E Flow**: Script generation ➔ Audio synthesis ➔ Audio ducking (-8.5 dB) check ➔ Wednesday 09:00 IST queueing ➔ Temporal gate release ➔ Webhook + Instagram publishing ➔ Verification of `PUBLISHED` state.

### Scenario 3: Luxury Real Estate & NRI Brokers
- **Industry & Language**: Real Estate Developers & Builders, Luxury English (`af_bella` / `en-IN-NeerjaNeural`).
- **Problem**: Losing ₹2.85 Cr - ₹15 Cr luxury beach villa and penthouse buyers due to 4-hour delay in sharing site visit dates and brochures.
- **Scheduled Slot**: Wednesday Slot 2 — 20:30 IST (Night High-Ticket Leisure).
- **CTA Hook**: "👇 COMMENT 'CLOSER' BELOW 👇 to get the ECR Villa Brochure & Sunday Site Visit Booking Agent."
- **WhatsApp Asset**: `ECR_Sea_Facing_Penthouse_Brochure.pdf`.
- **E2E Flow**: Script generation ➔ Character rig verification ➔ Wednesday 20:30 IST queueing ➔ Temporal dispatch ➔ Signature verification ➔ Instagram publishing ➔ State audit log verification.

### Scenario 4: EdTech Admissions Speed-to-Lead
- **Industry & Language**: EdTech & Career Bootcamps (Data Science & AI), Hinglish & Indian English (`en-IN-PrabhatNeural`).
- **Problem**: Students apply to 4 competing bootcamps simultaneously; the first counselor calling within 45 seconds gets the admission.
- **Scheduled Slot**: Thursday Slot 1 — 13:30 IST (Lunch Speed Teardown).
- **CTA Hook**: "👇 COMMENT 'CLOSER' BELOW 👇 for the Sub-45s Admissions Speed-to-Lead Make.com Blueprint."
- **WhatsApp Asset**: `Data_Science_Syllabus_Scholarship_Pass.pdf`.
- **E2E Flow**: Script generation ➔ Subtitle baseline check (Y=1360) ➔ Thursday 13:30 IST queueing ➔ Temporal gate ➔ Webhook payload delivery ➔ Mock Meta container polling & publish ➔ Verification.

### Scenario 5: B2B Agency Lead Gen / Media Buyer Defense
- **Industry & Language**: B2B Lead Gen & Performance Marketing Agencies, Indian English & Hinglish (`af_heart`).
- **Problem**: Agency burns ₹2.5L on Meta ads; client's sluggish telecallers dial 14 hours late and blame agency for "dead leads".
- **Scheduled Slot**: Friday Slot 1 — 09:15 IST (Morning Agency Client Defense).
- **CTA Hook**: "👇 COMMENT 'CLOSER' BELOW 👇 for the Agency Instant Auto-Dialer Setup Blueprint."
- **WhatsApp Asset**: `Agency_Instant_AutoDialer_Workflow.pdf`.
- **E2E Flow**: Script generation ➔ Multi-format export verification (1080p, 720p, 1:1, MP3, SRT) ➔ Friday 09:15 IST queueing ➔ Webhook dispatch ➔ Full lifecycle audit verification.

---

## 5. Coverage Thresholds

| Test Tier | Scope & Objective | Coverage Target | Verification Criteria |
|:---|:---|:---:|:---|
| **Tier 1: Features** | Happy-path verification of all 22 features | $\ge 5$ test assertions per feature category | All assertions pass, 100% compliant schemas |
| **Tier 2: Boundaries** | Edge cases, limits, corrupt data, clock drift | $\ge 5$ boundary/corner cases per feature category | Expected exceptions raised, errors properly formatted |
| **Tier 3: Combinations**| Pairwise & cross-feature integration | All major cross-subsystem interactions covered | Data handoffs between layers preserve integrity |
| **Tier 4: Scenarios**  | Real-world end-to-end industry pipelines | 5 complete distinct industry sector workflows | Full lifecycle from DRAFT to PUBLISHED verified |

---

## 6. Execution & CI Integration

### Local Execution:
```bash
python3 -m pytest tests/e2e/ -v --tb=short
```

### GitHub Actions Workflow Integration:
The test suite is integrated into `.github/workflows/reels_pipeline.yml` to gate automated batch generation and dispatch runs:
```yaml
- name: Run E2E Test Suite
  run: |
    python3 -m pytest tests/e2e/ -v
```
Any failure halts deployment, preventing corrupted or unscheduled reels from publishing.
