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
        "🤖 SEÑALES PRO M1\n\n"
        "Bot conectado correctamente.\n\n"
        "📊 /señal - Solicitar una señal\n"
        "📝 /resultado - Registrar resultado\n"
        "📈 /estadisticas - Ver estadísticas\n\n"
        "⚠️ Las señales se probarán primero en DEMO."
    )
    await update.message.reply_text(mensaje)


async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 ANALIZANDO EL MERCADO...\n\n"
        "⏳ El módulo de análisis M1 todavía está en configuración.\n"
        "No se enviará ninguna operación hasta tener una señal válida."
    )


async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 REGISTRO DE RESULTADO\n\n"
        "Esta función quedará conectada al sistema de estadísticas."
    )


async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 ESTADÍSTICAS\n\n"
        "Todavía no hay operaciones registradas."
    )


def main():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en las variables de entorno.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("señal", senal))
    app.add_handler(CommandHandler("resultado", resultado))
    app.add_handler(CommandHandler("estadísticas", estadisticas))

    print("🚀 Señales Pro M1 iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
