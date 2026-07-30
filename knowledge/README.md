# GGBH Knowledge Base

Customer-facing knowledge base for **Gulf Gateway Business Hub (GGBH)**'s Telegram bot. It powers
two things only:

1. **Speed-to-Lead qualification** — helping the bot hold a useful conversation with a prospective
   customer and recognize when they're a qualified lead (see `app/leads.py` / `app/llm.py`).
2. **Doubt clarification** — answering a customer's questions about UAE business setup and
   immigration/visa matters.

This knowledge base is **not** an internal operations manual. It intentionally does not cover ERP
click-steps, GDRFA portal navigation, internal email templates, or staff escalation workflows —
those are out of scope for a customer-facing bot.

## Files

- [`customer/business_setup_and_activities.md`](customer/business_setup_and_activities.md) — what
  business activities a customer can pursue, which activities need extra government approval, and
  the general company-setup process.
- [`customer/visa_and_immigration.md`](customer/visa_and_immigration.md) — visa eligibility (GCC
  exemption, age limits, Investor/Partner rules), required documents, health insurance, visa
  allocation, overstay fines, and refund policy.
- [`customer/nationality_document_requirements.md`](customer/nationality_document_requirements.md)
  — extra documents required by nationality, longer bank-statement nationalities, and passport-type
  restrictions.
- [`customer/designations_and_qualifications.md`](customer/designations_and_qualifications.md) —
  which visa designations require a MOFA-attested degree, the exceptions, and how qualifications are
  matched.

These four files are loaded directly into the bot's system prompt at startup (see
`app/prompts.py`) — editing a file here changes what the bot knows the next time it starts.

## What was intentionally left out

- **No credentials of any kind.**
- **No real personal names, phone numbers, addresses, or email domains.** Contact placeholders
  (`{{SUPPORT_EMAIL}}`, `{{SUPPORT_PHONE}}`, `{{OFFICE_ADDRESS}}`) should be filled in from
  `app/config.py` / environment variables, not hardcoded here.
- **No ERP workflows, GDRFA/portal click-steps, internal email templates, or staff escalation
  language** — this knowledge base serves customers, not internal operations staff.
- **No wholesale copy of the GDRFA Designation List or Qualifications Lookup spreadsheets** — both
  source PDFs had scrambled OCR text, so instead of risking silent transcription errors in
  visa-eligibility data, the *decision logic* is documented in
  `customer/designations_and_qualifications.md` and the original spreadsheets should be kept
  separately as the system of record.

## Known gaps (do not guess past these)

1. **A small set of specialized designations** have an unverified attested-degree requirement —
   flagged explicitly in `customer/designations_and_qualifications.md`. The bot should tell the
   customer this is being confirmed rather than answer yes/no.
2. **Bangladesh "outside the country" allowed-designations list** — the source spreadsheet was
   never supplied. Flagged in `customer/nationality_document_requirements.md`.
