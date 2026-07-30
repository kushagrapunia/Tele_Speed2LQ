import json
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook, load_workbook

from .config import LEADS_EXCEL_PATH

_HEADERS = ["Timestamp (UTC)", "Chat ID", "Telegram Username", "Name", "Contact", "Interest", "Notes"]

_leads_path = Path(LEADS_EXCEL_PATH)
_captured_state_path = _leads_path.with_name("captured_leads.json")


def _ensure_workbook() -> None:
    if _leads_path.exists():
        return
    _leads_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Leads"
    sheet.append(_HEADERS)
    workbook.save(_leads_path)


def _load_captured() -> set[str]:
    if not _captured_state_path.exists():
        return set()
    return set(json.loads(_captured_state_path.read_text(encoding="utf-8")))


def _save_captured(captured: set[str]) -> None:
    _captured_state_path.write_text(json.dumps(sorted(captured)), encoding="utf-8")


def is_lead_captured(chat_id: str) -> bool:
    return chat_id in _load_captured()


def record_lead(chat_id: str, telegram_username: str, name: str, contact: str, interest: str, notes: str = "") -> None:
    _ensure_workbook()

    workbook = load_workbook(_leads_path)
    sheet = workbook["Leads"]
    sheet.append([
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
        chat_id,
        telegram_username,
        name,
        contact,
        interest,
        notes,
    ])
    workbook.save(_leads_path)

    captured = _load_captured()
    captured.add(chat_id)
    _save_captured(captured)
