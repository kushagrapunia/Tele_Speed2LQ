import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")
LEADS_EXCEL_PATH = os.getenv("LEADS_EXCEL_PATH", "data/leads.xlsx")
INACTIVITY_TIMEOUT_SECONDS = int(os.getenv("INACTIVITY_TIMEOUT_SECONDS", "120"))
