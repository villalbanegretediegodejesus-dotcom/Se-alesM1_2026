import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🤖 SENALES PRO M1\n\n"
        "Bot conectado correctamente.\n\n"
        "📊 /senal - Solicitar una senal\n"
        "📝 /resultado - Registrar resultado\n"
        "📈 /estadisticas - Ver estadisticas\n\n"
        "⚠️ Las senales se probarán primero en DEMO."
    )
    await update.message.reply_text(mensaje)


async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 ANALIZANDO EL MERCADO...\n\n"
        "⏳ El modulo de analisis M1 todavia esta en configuracion.\n"
        "No se enviara ninguna operacion hasta tener una senal valida."
    )


async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 REGISTRO DE RESULTADO\n\n"
        "Esta funcion quedara conectada al sistema de estadísticas."
    )


async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 ESTADISTICAS\n\n"
        "Todavia no hay operaciones registradas."
    )


def main():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en las variables de entorno.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("senal", senal))
    app.add_handler(CommandHandler("resultado", resultado))
    app.add_handler(CommandHandler("estadisticas", estadisticas))

    print("🚀 Senales Pro M1 iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
