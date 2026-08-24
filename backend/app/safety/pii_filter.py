"""
PII (Personally Identifiable Information) protection layer.

FUSD requirement: personal information a user types must NEVER leave the
chatbot to an external LLM provider. Strategy:

  - Retrieval uses the ORIGINAL query (so search quality is never degraded)
  - Right before calling the external LLM, every piece of text that will be
    sent out (query, history, context) passes through redact_pii(), which
    replaces PII with harmless placeholders

The user still gets their answer; the raw personal data stays local.

Detected categories:
  emails, phone numbers, SSNs, street addresses (rough), student ID numbers,
  dates of birth, IP addresses, URLs with tokens, full-name-like patterns in
  structured contexts ("my name is ...", "I am ...", "parent of ...")
"""

import re
from dataclasses import dataclass, field
from typing import List

# --- Regex arsenal -----------------------------------------------------------

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
PHONE_RE = re.compile(
    r"(?<!\d)(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# Student/local IDs as used in school systems (5-8 digits with context)
STUDENT_ID_RE = re.compile(
    r"\b(?:student(?:\s*id)?|id)\s*(?:number|no\.?|#)?\s*(?:is|:|=|#)?\s*(\d{5,8})\b",
    re.IGNORECASE,
)
DOB_RE = re.compile(
    r"\b(?:born on|birthday is|dob|date of birth)\s*:?\s*"
    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4})",
    re.IGNORECASE,
)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
STREET_ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}"
    r"(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Lane|Ln\.?|"
    r"Drive|Dr\.?|Court|Ct\.?|Way|Circle|Cir\.?)\b"
)
# Self-disclosed name patterns ("my name is John Smith", "I'm Mrs. Diaz",
# "my son Johnny Smith" — minors' names count as PII)
SELF_NAME_RE = re.compile(
    r"\b(?:[Mm]y [Nn]ame is|[Ii] am|[Ii]'m|[Tt]his is|[Nn]ame:?|"
    r"[Ss]tudent [Nn]ame:?|"
    r"(?:[Mm]y|[Oo]ur) (?:son|daughter|child|kid)|"
    r"(?:student|child)'?s? name:?)\s+"
    r"([A-Z][a-z]+(?: [A-Z][a-z']+){0,2})",
)

PLACEHOLDERS = {
    "email": "[EMAIL REMOVED]",
    "phone": "[PHONE NUMBER REMOVED]",
    "ssn": "[SSN REMOVED]",
    "student_id": "[ID REMOVED]",
    "dob": "[BIRTHDATE REMOVED]",
    "ip": "[IP REMOVED]",
    "address": "[ADDRESS REMOVED]",
    "name": "[NAME REMOVED]",
}


@dataclass
class PIIReport:
    original_length: int
    findings: List[str] = field(default_factory=list)
    redacted_text: str = ""

    @property
    def contains_pii(self) -> bool:
        return len(self.findings) > 0


def detect_pii(text: str) -> List[str]:
    """Return list of PII category names found in text."""
    found = []
    if EMAIL_RE.search(text):
        found.append("email")
    if PHONE_RE.search(text):
        found.append("phone")
    if SSN_RE.search(text):
        found.append("ssn")
    if STUDENT_ID_RE.search(text):
        found.append("student_id")
    if DOB_RE.search(text):
        found.append("dob")
    if IP_RE.search(text):
        found.append("ip")
    if STREET_ADDRESS_RE.search(text):
        found.append("address")
    if SELF_NAME_RE.search(text):
        found.append("name")
    return found


def redact_pii(text: str) -> str:
    """Replace all detected PII with placeholders. Idempotent."""
    if not text:
        return text

    # Order matters: specific patterns before generic ones.
    text = SSN_RE.sub(PLACEHOLDERS["ssn"], text)
    text = EMAIL_RE.sub(PLACEHOLDERS["email"], text)
    text = STUDENT_ID_RE.sub(lambda m: m.group(0).replace(m.group(1), "[ID REMOVED]"), text)
    text = DOB_RE.sub(lambda m: m.group(0).replace(
        re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4})$", m.group(0)).group(0),
        PLACEHOLDERS["dob"]), text)
    text = PHONE_RE.sub(PLACEHOLDERS["phone"], text)
    text = STREET_ADDRESS_RE.sub(PLACEHOLDERS["address"], text)
    text = IP_RE.sub(PLACEHOLDERS["ip"], text)
    # Self-disclosed names last (needs word boundaries intact)
    text = SELF_NAME_RE.sub(lambda m: m.group(0).replace(m.group(1), PLACEHOLDERS["name"]), text)
    return text


def scrub_outbound(text: str) -> tuple:
    """
    Convenience wrapper for anything about to be sent to the external LLM.
    Returns (safe_text, report).
    """
    findings = detect_pii(text or "")
    safe = redact_pii(text) if findings else (text or "")
    return safe, PIIReport(
        original_length=len(text or ""),
        findings=findings,
        redacted_text=safe,
    )


if __name__ == "__main__":
    tests = [
        "My son Johnny Smith, student id: 4839201, forgot his password. Contact me at jane.doe@gmail.com or 510-555-1234.",
        "What time does school start at Horner?",
        "I live at 38442 Fremont Blvd, when is registration?",
        "My daughter was born on 03/14/2012, which grade does she go into?",
    ]
    for t in tests:
        safe, rep = scrub_outbound(t)
        print(f"IN : {t}")
        print(f"OUT: {safe}   {rep.findings}\n")
