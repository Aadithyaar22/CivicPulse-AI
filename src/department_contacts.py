"""Department -> recipient email(s) directory for department-scoped weekly
reports (see scheduled_brief in main.py).

Each department can list multiple recipients, which covers routing to
sub-offices/subsidiaries within one department, not just a single inbox.

For the demo, every department routes to the same inbox so nothing goes to a
real official's address -- but the routing logic itself is fully real: each
recipient only gets a brief scoped to their own department's complaints, not
the whole city's data. Point individual departments at real addresses here
before a real deployment.
"""

from __future__ import annotations

from .utils import normalize_text

_DEMO_INBOX = "aadithyaar22@gmail.com"

DEPARTMENT_CONTACTS: dict[str, list[str]] = {
    "Sanitation Dept": [_DEMO_INBOX],
    "Water Board": [_DEMO_INBOX],
    "Public Works": [_DEMO_INBOX],
    "Environment Cell": [_DEMO_INBOX],
    "Health Dept": [_DEMO_INBOX],
}

_NORMALIZED_CONTACTS = {normalize_text(k): v for k, v in DEPARTMENT_CONTACTS.items()}


def recipients_for(department: str) -> list[str]:
    """Real, non-empty recipients for a department, or [] if none configured
    -- callers must treat [] as "skip this department", never guess/default."""
    return _NORMALIZED_CONTACTS.get(normalize_text(department), [])
