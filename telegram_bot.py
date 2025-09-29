import logging
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ====== CONFIG (SOLO PRUEBAS) ======
OPENAI_API_KEY = ""        # ⚠️ Solo para pruebas
TELEGRAM_BOT_TOKEN = "" # ⚠️ Solo para pruebas
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "Eres un asistente útil que responde en español de forma clara y breve."
MAX_TURNS = 12  # Límite de turnos por chat para mantener el contexto chico

client = OpenAI(api_key=OPENAI_API_KEY)

# Memoria simple por chat_id: { chat_id: [ {role, content}, ... ] }
CHAT_MEMORY = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_history(chat_id: int):
    if chat_id not in CHAT_MEMORY:
        CHAT_MEMORY[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return CHAT_MEMORY[chat_id]

def trim_history(chat_id: int):
    hist = get_history(chat_id)
    # Mantén system + últimos turnos
    if len(hist) > 2 * MAX_TURNS + 1:
        CHAT_MEMORY[chat_id] = [hist[0]] + hist[-2*MAX_TURNS:]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    CHAT_MEMORY[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("¡Hola! Soy tu bot con OpenAI. Envíame un mensaje y te respondo 😊")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    CHAT_MEMORY[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("Contexto reiniciado ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()
    hist = get_history(chat_id)

    # Agrega turno del usuario
    hist.append({"role": "user", "content": user_text})
    trim_history(chat_id)

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=hist,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        logger.exception("OpenAI error")
        answer = f"⚠️ Error con OpenAI: {e}"

    # Agrega turno del asistente y responde
    hist.append({"role": "assistant", "content": answer})
    trim_history(chat_id)

    await update.message.reply_text(answer)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
