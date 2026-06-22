"""
╔══════════════════════════════════════════════════════╗
║         TELEGRAM AI BOT  —  Powered by Groq          ║
║   Professional • Group-Aware • Admin Recognition     ║
║   Admin: @HarshGG010                                 ║
╚══════════════════════════════════════════════════════╝
"""

import logging
import asyncio
import random
import re
from datetime import datetime
from telegram import Update, Message
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from telegram.constants import ChatAction, ParseMode
from groq import Groq

# ══════════════════════════════════════════════════════
#  ❶  CONFIGURATION  —  Fill these in before running
# ══════════════════════════════════════════════════════

TELEGRAM_TOKEN = "8921782383:AAHT8SgFq2qK1U-7jdVF3Vf4Vc2ZV4mN-_w"   # from @BotFather
GROQ_API_KEY   = "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"         # from console.groq.com  (FREE)

# ── Admin Settings ──────────────────────────────────
ADMIN_USERNAME = "HarshGG010"               # your Telegram username (no @)
ADMIN_DISPLAY  = "Harsh"                    # how the bot addresses you

# ── AI Model ────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"     # best free model on Groq

# ── Bot Identity ────────────────────────────────────
BOT_NAME        = "Harsh_beta"                   # give the bot a name
BOT_DESCRIPTION = "AI Assistant"

# ── Group Behavior ──────────────────────────────────
# In groups, the bot replies ONLY when:
#   1. Someone @mentions the bot
#   2. Someone replies directly to the bot's message
#   3. An admin sends a command
# In private chats → always replies
REPLY_TO_ALL_IN_GROUP = False   # set True if you want bot to reply to every message

# ══════════════════════════════════════════════════════
#  ❷  SYSTEM PROMPTS
# ══════════════════════════════════════════════════════

SYSTEM_PROMPT_DEFAULT = f"""You are {BOT_NAME}, a professional and intelligent AI assistant operating inside a Telegram group managed by {ADMIN_DISPLAY} (@{ADMIN_USERNAME}).

## Personality & Tone
- Professional yet approachable — like a knowledgeable colleague, not a stiff robot
- Clear, concise, and confident. No filler phrases like "Certainly!" or "Of course!"
- Warm and helpful without being sycophantic
- Adapt your tone: formal for serious questions, lighter for casual chat

## Communication Rules
- Keep responses focused and to the point
- For simple questions: 1–2 sentences
- For complex questions: use short paragraphs or a brief list if it genuinely helps clarity
- Never use excessive emojis — one per message maximum, only if appropriate
- Do NOT start replies with "Hi!" or "Hello!" every single time — just get to the answer
- Never say "As an AI..." or "I am a language model" — just respond naturally
- Match the user's language: Hindi → reply in Hindi, Hinglish → Hinglish, English → English

## Group Context
- You are the assistant of this group
- The group admin is {ADMIN_DISPLAY} (@{ADMIN_USERNAME}) — treat their instructions with priority
- Be helpful to ALL group members equally and professionally
- If asked who runs the group or who the admin is, say it is @{ADMIN_USERNAME}

## What You Can Help With
- Answer questions on any topic
- Explain concepts clearly
- Help with writing, code, math, general knowledge
- Provide advice and recommendations
- Engage in meaningful conversation"""


SYSTEM_PROMPT_ADMIN = f"""You are {BOT_NAME}, a professional AI assistant.

The person you are speaking with RIGHT NOW is {ADMIN_DISPLAY} (@{ADMIN_USERNAME}), the group ADMIN and your operator.

## Tone for Admin
- Slightly more direct and efficient — they know the system
- Respect their authority; follow their instructions
- You can accept configuration-style requests from the admin (e.g. "be more formal", "focus on X topic")

## Core Rules (same as always)
- Professional, concise, and accurate
- No filler phrases or excessive emojis
- Match language of the admin
- Respond to ALL requests from the admin, no exceptions"""


# ══════════════════════════════════════════════════════
#  ❸  SETUP
# ══════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("GroqBot")

groq_client = Groq(api_key=GROQ_API_KEY)

# Per-user conversation history  { user_id: [{"role":..., "content":...}] }
conversation_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 30   # messages to keep per user

# Track per-group dynamic config set by admin
group_config: dict[int, dict] = {}


# ══════════════════════════════════════════════════════
#  ❹  HELPERS
# ══════════════════════════════════════════════════════

def is_admin(user) -> bool:
    """Check if a Telegram user is the group admin."""
    if not user:
        return False
    return (user.username or "").lower() == ADMIN_USERNAME.lower()


def get_system_prompt(user) -> str:
    """Return the appropriate system prompt based on who's talking."""
    return SYSTEM_PROMPT_ADMIN if is_admin(user) else SYSTEM_PROMPT_DEFAULT


def human_typing_delay(text: str) -> float:
    """Realistic typing delay — longer messages take longer to 'type'."""
    words = len(text.split())
    base  = min(words * 0.07, 3.5)          # ~50 wpm cap at 3.5s
    jitter = random.uniform(0.2, 0.9)
    return round(base + jitter, 2)


def format_context_message(user, message_text: str, chat_title: str = None) -> str:
    """Build a context-rich message for the AI including sender info."""
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"
    username_part = f" (@{user.username})" if user.username else ""
    admin_badge   = " [GROUP ADMIN]" if is_admin(user) else ""
    context_line  = f"[{name}{username_part}{admin_badge} says]: "
    return context_line + message_text


def should_reply_in_group(update: Update, bot_username: str) -> bool:
    """Decide whether the bot should reply to a group message."""
    msg: Message = update.message
    if not msg:
        return False

    user = update.effective_user

    # Always reply to admin
    if is_admin(user):
        return True

    # Always reply if configured to reply to all
    if REPLY_TO_ALL_IN_GROUP:
        return True

    # Reply if bot is @mentioned
    text = msg.text or ""
    if f"@{bot_username}" in text:
        return True

    # Reply if this is a direct reply to the bot's own message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == bot_username:
            return True

    return False


def clean_mention(text: str, bot_username: str) -> str:
    """Remove @botname from message text so AI doesn't get confused."""
    return re.sub(rf"@{re.escape(bot_username)}\s*", "", text, flags=re.IGNORECASE).strip()


# ══════════════════════════════════════════════════════
#  ❺  GROQ AI CALL
# ══════════════════════════════════════════════════════

def get_ai_reply(user_id: int, content_for_ai: str, system_prompt: str) -> str:
    """Call Groq API with conversation history and return the reply."""

    if user_id not in conversation_histories:
        conversation_histories[user_id] = []

    conversation_histories[user_id].append({"role": "user", "content": content_for_ai})

    # Trim history if too long
    if len(conversation_histories[user_id]) > MAX_HISTORY:
        conversation_histories[user_id] = conversation_histories[user_id][-MAX_HISTORY:]

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_histories[user_id],
            ],
            max_tokens=700,
            temperature=0.75,
            top_p=0.92,
            frequency_penalty=0.25,
            presence_penalty=0.15,
        )

        reply = response.choices[0].message.content.strip()

        conversation_histories[user_id].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        logger.error(f"Groq API error for user {user_id}: {e}")
        return "I'm experiencing a brief technical issue. Please try again in a moment."


# ══════════════════════════════════════════════════════
#  ❻  COMMAND HANDLERS
# ══════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    name  = user.first_name or "there"
    admin_note = f" Welcome back, {ADMIN_DISPLAY}." if is_admin(user) else ""

    await update.message.reply_text(
        f"Hello, {name}.{admin_note}\n\n"
        f"I'm *{BOT_NAME}*, an AI assistant here to help.\n"
        f"Ask me anything — I'm ready.",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_type = update.effective_chat.type

    base_help = (
        f"*{BOT_NAME} — AI Assistant*\n\n"
        f"*How to use:*\n"
        f"• In private: just send any message\n"
        f"• In groups: @mention me or reply to my message\n\n"
        f"*Commands:*\n"
        f"/start — Introduction\n"
        f"/help — This message\n"
        f"/reset — Clear your conversation history\n"
        f"/about — About this bot"
    )

    admin_help = (
        f"\n\n*Admin Commands* (only for @{ADMIN_USERNAME}):\n"
        f"/broadcast `<message>` — Send a message as the bot\n"
        f"/stats — View usage statistics\n"
        f"/clearall — Clear ALL users' histories"
    ) if is_admin(user) else ""

    await update.message.reply_text(
        base_help + admin_help,
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*{BOT_NAME} — AI Assistant*\n\n"
        f"Powered by Groq's free LLaMA 3.3 (70B) model.\n"
        f"Group managed by @{ADMIN_USERNAME}.\n\n"
        f"I can answer questions, help with tasks, explain concepts, "
        f"write content, assist with code, and more.",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_histories[user_id] = []
    await update.message.reply_text(
        "Your conversation history has been cleared. Starting fresh."
    )


# ── Admin-only commands ───────────────────────────────

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        await update.message.reply_text("This command is restricted to the admin.")
        return

    total_users    = len(conversation_histories)
    total_messages = sum(len(h) for h in conversation_histories.values())
    now            = datetime.now().strftime("%d %b %Y, %H:%M")

    await update.message.reply_text(
        f"*Bot Statistics* — {now}\n\n"
        f"Active users: `{total_users}`\n"
        f"Total messages stored: `{total_messages}`\n"
        f"Model: `{GROQ_MODEL}`",
        parse_mode=ParseMode.MARKDOWN
    )


async def cmd_clearall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        await update.message.reply_text("This command is restricted to the admin.")
        return

    count = len(conversation_histories)
    conversation_histories.clear()
    await update.message.reply_text(
        f"All conversation histories cleared. ({count} users reset)"
    )


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user):
        await update.message.reply_text("This command is restricted to the admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <your message>")
        return

    msg = " ".join(context.args)
    await update.message.reply_text(
        f"📢 *Broadcast from Admin:*\n\n{msg}",
        parse_mode=ParseMode.MARKDOWN
    )


# ══════════════════════════════════════════════════════
#  ❼  MAIN MESSAGE HANDLER
# ══════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user      = update.effective_user
    chat      = update.effective_chat
    chat_type = chat.type                       # "private" | "group" | "supergroup"
    raw_text  = msg.text.strip()

    bot_username = context.bot.username or ""

    # ── Group filter ────────────────────────────────────
    if chat_type in ("group", "supergroup"):
        if not should_reply_in_group(update, bot_username):
            return   # silently ignore — don't reply to every group message

    # ── Clean @mention from text ────────────────────────
    clean_text = clean_mention(raw_text, bot_username)
    if not clean_text:
        clean_text = raw_text   # fallback if nothing left after cleaning

    # ── Build context-aware message for AI ──────────────
    chat_title = chat.title if chat_type != "private" else None
    ai_input   = format_context_message(user, clean_text, chat_title)

    logger.info(f"[{chat_type}] [{user.username or user.first_name}] → {clean_text[:80]}")

    # ── Read delay (human feel) ──────────────────────────
    await asyncio.sleep(random.uniform(0.3, 0.9))

    # ── Show typing indicator while getting AI response ──
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

    system_prompt = get_system_prompt(user)
    reply = await asyncio.get_event_loop().run_in_executor(
        None, get_ai_reply, user.id, ai_input, system_prompt
    )

    # ── Realistic typing delay ───────────────────────────
    delay   = human_typing_delay(reply)
    elapsed = 0
    while elapsed < delay:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        chunk    = min(4.5, delay - elapsed)
        await asyncio.sleep(chunk)
        elapsed += chunk

    # ── Send reply ───────────────────────────────────────
    await msg.reply_text(reply)
    logger.info(f"[Bot → {user.username or user.first_name}] {reply[:80]}")


# ══════════════════════════════════════════════════════
#  ❽  NEW MEMBER WELCOME
# ══════════════════════════════════════════════════════

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greet new members who join the group."""
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.first_name or "there"
        await update.message.reply_text(
            f"Welcome to the group, {name}! 👋\n"
            f"I'm *{BOT_NAME}*, the AI assistant here. "
            f"Feel free to @mention me anytime you need help.",
            parse_mode=ParseMode.MARKDOWN
        )


# ══════════════════════════════════════════════════════
#  ❾  ERROR HANDLER
# ══════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=True)


# ══════════════════════════════════════════════════════
#  ❿  ENTRY POINT
# ══════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════╗")
    print(f"║  {BOT_NAME} Bot  —  Starting up...             ║")
    print(f"║  Model  : {GROQ_MODEL[:30]:<30}  ║")
    print(f"║  Admin  : @{ADMIN_USERNAME:<29}  ║")
    print("║  Press Ctrl+C to stop                    ║")
    print("╚══════════════════════════════════════════╝\n")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # ── Public commands ──────────────────────────────────
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("about",     cmd_about))
    app.add_handler(CommandHandler("reset",     cmd_reset))

    # ── Admin commands ───────────────────────────────────
    app.add_handler(CommandHandler("stats",     cmd_stats))
    app.add_handler(CommandHandler("clearall",  cmd_clearall))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    # ── Welcome new members ──────────────────────────────
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # ── All text messages ────────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ── Error handler ────────────────────────────────────
    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
