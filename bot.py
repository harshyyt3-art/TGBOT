"""
╔══════════════════════════════════════════════════════╗
║         TELEGRAM AI BOT  —  Powered by Groq          ║
║   Professional • Replies in Groups & DMs             ║
║   Admin: @HarshGG010                                 ║
╚══════════════════════════════════════════════════════╝
"""

import logging
import asyncio
import random
import re
import os
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from telegram.constants import ChatAction, ParseMode
from groq import Groq

# ══════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")

if not TELEGRAM_TOKEN:
    sys.exit("❌  TELEGRAM_TOKEN is not set.")
if not GROQ_API_KEY:
    sys.exit("❌  GROQ_API_KEY is not set.")

ADMIN_USERNAME = "HarshGG010"
ADMIN_DISPLAY  = "Harsh"
GROQ_MODEL     = "llama-3.3-70b-versatile"
BOT_NAME       = "Aria"
MAX_HISTORY    = 30

# ══════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ══════════════════════════════════════════════════════

SYSTEM_PROMPT = f"""You are {BOT_NAME}, a smart and professional AI assistant in a Telegram group managed by {ADMIN_DISPLAY} (@{ADMIN_USERNAME}).

Personality:
- Professional but friendly — like a helpful colleague
- Concise and clear — no unnecessary filler like "Certainly!" or "Of course!"
- Never say "As an AI..." — just answer naturally
- Match the user's language automatically (Hindi, Hinglish, English, etc.)
- One emoji max per message, only when it fits

For simple questions: 1-2 sentences.
For complex questions: short paragraphs or brief lists only if needed.

The group admin is @{ADMIN_USERNAME} — treat their instructions with priority.
If anyone asks who the admin is, say @{ADMIN_USERNAME}."""

SYSTEM_PROMPT_ADMIN = f"""You are {BOT_NAME}, an AI assistant. You are speaking with {ADMIN_DISPLAY} (@{ADMIN_USERNAME}), your operator and group admin.
Be direct, efficient, and follow their instructions. No filler phrases. Match their language."""

# ══════════════════════════════════════════════════════
#  SETUP
# ══════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("AriaBot")

groq_client = Groq(api_key=GROQ_API_KEY)
conversation_histories: dict[int, list[dict]] = {}


# ══════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════

def is_admin(user) -> bool:
    if not user or not user.username:
        return False
    return user.username.lower() == ADMIN_USERNAME.lower()


def typing_delay(text: str) -> float:
    words = len(text.split())
    return min(words * 0.06, 3.0) + random.uniform(0.2, 0.8)


def get_ai_reply(user_id: int, message: str, is_admin_user: bool) -> str:
    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({"role": "user", "content": message})

    if len(conversation_histories[user_id]) > MAX_HISTORY:
        conversation_histories[user_id] = conversation_histories[user_id][-MAX_HISTORY:]

    system = SYSTEM_PROMPT_ADMIN if is_admin_user else SYSTEM_PROMPT

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                *conversation_histories[user_id],
            ],
            max_tokens=700,
            temperature=0.75,
            top_p=0.92,
            frequency_penalty=0.25,
        )
        reply = response.choices[0].message.content.strip()
        conversation_histories[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "Sorry, I'm having a brief issue. Please try again in a moment."


# ══════════════════════════════════════════════════════
#  COMMANDS
# ══════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "there"
    note = f" Welcome back, {ADMIN_DISPLAY}." if is_admin(update.effective_user) else ""
    await update.message.reply_text(
        f"Hello, {name}.{note}\n\nI'm *{BOT_NAME}*, your AI assistant. Ask me anything.",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*{BOT_NAME} — AI Assistant*\n\n"
        "Just send any message and I'll reply.\n\n"
        "*Commands:*\n"
        "/start — Introduction\n"
        "/reset — Clear your chat history\n"
        "/about — About this bot\n"
        "/stats — Usage stats (admin only)",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*{BOT_NAME}* — powered by Groq's free LLaMA 3.3 70B model.\n"
        f"Group managed by @{ADMIN_USERNAME}.",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversation_histories[update.effective_user.id] = []
    await update.message.reply_text("Conversation history cleared. Fresh start!")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        await update.message.reply_text("This command is for the admin only.")
        return
    total = sum(len(h) for h in conversation_histories.values())
    await update.message.reply_text(
        f"*Stats*\nActive users: `{len(conversation_histories)}`\n"
        f"Total messages: `{total}`\nModel: `{GROQ_MODEL}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_clearall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        return
    count = len(conversation_histories)
    conversation_histories.clear()
    await update.message.reply_text(f"Cleared all histories. ({count} users reset)")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user) or not context.args:
        return
    await update.message.reply_text(
        f"📢 *Message from Admin:*\n\n{' '.join(context.args)}",
        parse_mode=ParseMode.MARKDOWN
    )


# ══════════════════════════════════════════════════════
#  MAIN MESSAGE HANDLER — replies in ALL chats
# ══════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Safety checks
    if not update.message:
        return
    if not update.message.text:
        return
    if not update.effective_user:
        return

    user      = update.effective_user
    chat      = update.effective_chat
    text      = update.message.text.strip()
    chat_type = chat.type   # "private", "group", "supergroup", "channel"

    # Skip empty messages
    if not text:
        return

    # Remove @botmention from text if present
    bot_username = context.bot.username or ""
    clean_text = re.sub(rf"@{re.escape(bot_username)}", "", text, flags=re.IGNORECASE).strip()
    if not clean_text:
        clean_text = text

    # Add sender context so AI knows who's talking
    name = user.first_name or "User"
    username_str = f"@{user.username}" if user.username else name
    admin_tag = " [ADMIN]" if is_admin(user) else ""
    ai_message = f"[{username_str}{admin_tag}]: {clean_text}"

    logger.info(f"[{chat_type}] {username_str} → {clean_text[:80]}")

    # Human-like read delay
    await asyncio.sleep(random.uniform(0.3, 0.8))

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

    # Get AI reply
    reply = await asyncio.get_event_loop().run_in_executor(
        None, get_ai_reply, user.id, ai_message, is_admin(user)
    )

    # Typing delay based on reply length
    delay = typing_delay(reply)
    elapsed = 0
    while elapsed < delay:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        chunk = min(4.0, delay - elapsed)
        await asyncio.sleep(chunk)
        elapsed += chunk

    # Send reply
    await update.message.reply_text(reply)
    logger.info(f"[Bot → {username_str}] {reply[:80]}")


# ══════════════════════════════════════════════════════
#  WELCOME NEW MEMBERS
# ══════════════════════════════════════════════════════

async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await update.message.reply_text(
            f"Welcome, {member.first_name}! 👋\n"
            f"I'm *{BOT_NAME}*, the AI assistant here. Feel free to talk to me anytime.",
            parse_mode=ParseMode.MARKDOWN
        )


# ══════════════════════════════════════════════════════
#  ERROR HANDLER
# ══════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=False)


# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════

def main():
    print(f"✅  {BOT_NAME} Bot starting...")
    print(f"    Model : {GROQ_MODEL}")
    print(f"    Admin : @{ADMIN_USERNAME}")
    print(f"    Replies in: private chats + ALL group messages\n")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("about",     cmd_about))
    app.add_handler(CommandHandler("reset",     cmd_reset))
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("clearall",  cmd_clearall))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member
    ))

    # ✅ This catches ALL text in private + group + supergroup
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))

    app.add_error_handler(error_handler)

    print("🤖  Bot is running. Press Ctrl+C to stop.\n")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
