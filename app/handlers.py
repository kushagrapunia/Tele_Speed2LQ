import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .config import INACTIVITY_TIMEOUT_SECONDS, TELEGRAM_BOT_TOKEN
from .llm import get_conversation_summary, get_llm_reply
from .prompts import FAQS

logger = logging.getLogger(__name__)

conversation_store = {}
_idle_close_tasks: dict[str, asyncio.Task] = {}


async def _send_formatted(bot, chat_id: int, text: str) -> None:
    """Send with Telegram HTML formatting; fall back to plain text if the model produced unparsable markup."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
    except BadRequest:
        logger.warning("HTML parse failed for chat %s, resending as plain text", chat_id)
        await bot.send_message(chat_id=chat_id, text=text)


async def _close_idle_chat(chat_id: str, bot) -> None:
    await asyncio.sleep(INACTIVITY_TIMEOUT_SECONDS)

    history = conversation_store.pop(chat_id, None)
    _idle_close_tasks.pop(chat_id, None)
    if not history:
        return

    summary = get_conversation_summary(history)
    await _send_formatted(
        bot,
        int(chat_id),
        f"⏳ Since I haven't heard back, I'll close this chat here.\n\n<b>Summary:</b> {summary}\n\nFeel free to message me again anytime to continue. 👋",
    )


def _reschedule_idle_close(chat_id: str, bot) -> None:
    existing_task = _idle_close_tasks.get(chat_id)
    if existing_task and not existing_task.done():
        existing_task.cancel()
    _idle_close_tasks[chat_id] = asyncio.create_task(_close_idle_chat(chat_id, bot))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[
        InlineKeyboardButton("💼 Setup cost", callback_data="faq_cost"),
        InlineKeyboardButton("📄 Documents", callback_data="faq_docs"),
    ], [
        InlineKeyboardButton("⏱ Timeline", callback_data="faq_timeline"),
        InlineKeyboardButton("🛂 Visas", callback_data="faq_visa"),
    ], [
        InlineKeyboardButton("📅 Book consultation", callback_data="book_call"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to Gulf Gateway Business Hub 👋 I can answer setup questions and book a free consultation. Tap a topic below or type your question.",
        reply_markup=reply_markup,
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = str(update.message.chat_id)
    user_text = update.message.text
    user = update.message.from_user
    telegram_username = (user.username or user.full_name or "") if user else ""
    history = conversation_store.get(chat_id, [])

    reply = get_llm_reply(user_text, history, chat_id=chat_id, telegram_username=telegram_username)
    conversation_store[chat_id] = history + [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
    await _send_formatted(context.bot, update.message.chat_id, reply)

    _reschedule_idle_close(chat_id, context.bot)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    data = query.data
    if data in FAQS:
        await query.edit_message_text(FAQS[data])
    elif data == "book_call":
        await query.edit_message_text("I can help you book a consultation. Please share your full name and preferred contact details.")


def build_application() -> object:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    from telegram.ext import Application

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    return application
