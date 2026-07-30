from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from .leads import is_lead_captured, record_lead
from .prompts import SYSTEM_PROMPT

RECORD_LEAD_TOOL = {
    "name": "record_qualified_lead",
    "description": (
        "Call this exactly once, when the visitor has given you (a) their name, (b) a way to reach "
        "them (phone number, email, or Telegram handle), and (c) what they're interested in (e.g. "
        "business setup, a specific visa type, or an immigration doubt). Do not call this more than "
        "once in the same conversation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The visitor's name"},
            "contact": {"type": "string", "description": "Phone number, email, or Telegram handle to reach the visitor"},
            "interest": {
                "type": "string",
                "description": "Short label for what they want, e.g. 'Mainland company setup', 'Investor visa', 'Attested-degree doubt'",
            },
            "notes": {"type": "string", "description": "One or two sentence summary of their situation, drawn from the conversation"},
        },
        "required": ["name", "contact", "interest"],
    },
}


def get_llm_reply(
    user_message: str,
    conversation_history: list | None = None,
    chat_id: str | None = None,
    telegram_username: str = "",
) -> str:
    if not ANTHROPIC_API_KEY:
        return "LLM is not configured yet. Set ANTHROPIC_API_KEY first."

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = list(conversation_history or []) + [{"role": "user", "content": user_message}]

    request_kwargs = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2048,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    if chat_id is None or not is_lead_captured(chat_id):
        request_kwargs["tools"] = [RECORD_LEAD_TOOL]

    response = client.messages.create(**request_kwargs)

    if response.stop_reason == "tool_use":
        tool_use = next(block for block in response.content if block.type == "tool_use")
        if tool_use.name == "record_qualified_lead" and chat_id is not None:
            lead = tool_use.input
            record_lead(
                chat_id=chat_id,
                telegram_username=telegram_username,
                name=lead.get("name", ""),
                contact=lead.get("contact", ""),
                interest=lead.get("interest", ""),
                notes=lead.get("notes", ""),
            )

        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": "Lead recorded."}],
        })
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

    text_block = next((block for block in response.content if block.type == "text"), None)
    return text_block.text.strip() if text_block else "Thanks for reaching out — a GGBH consultant will follow up with you shortly."


def get_conversation_summary(conversation_history: list) -> str:
    if not ANTHROPIC_API_KEY or not conversation_history:
        return "No summary available."

    transcript = "\n".join(f"{turn['role']}: {turn['content']}" for turn in conversation_history)
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        system=(
            "Summarize the following customer conversation with a business-setup consultancy in 2-3 "
            "short sentences: what the visitor asked about, and what (if anything) was resolved or "
            "left open. Write it for the visitor to read, addressing them as 'you'."
        ),
        messages=[{"role": "user", "content": transcript}],
    )
    text_block = next((block for block in response.content if block.type == "text"), None)
    return text_block.text.strip() if text_block else "No summary available."
