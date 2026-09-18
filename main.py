import os
import logging
import threading

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Credenciales para IQ Option.
# Se usarán más adelante mediante variables de entorno.
IQ_USERNAME = os.environ.get("IQ_USERNAME")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

# Render proporciona PORT automáticamente.
PORT = int(os.environ.get("PORT", "8080"))


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ============================================================
# SERVIDOR WEB PARA RENDER
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot activo", 200


@app.route("/health")
def health():
    return "OK", 200


def iniciar_servidor_web():
    """
    Inicia Flask en un hilo separado para que Render
    detecte el puerto HTTP mientras Telegram trabaja
    mediante Long Polling.
    """
    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False
    )


# ============================================================
# COMANDO /start
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 SENALES PRO M1\n\n"
        "Bot conectado correctamente.\n\n"
        "Comandos disponibles:\n"
        "/senal - Solicitar una senal de operacion\n"
        "/senal - Solicitar una senal de operacion\n"
        "/resultado - Registrar resultado de la operacion\n"
        "/estadisticas - Ver estadísticas de las operaciones\n\n"
        "Las senales se probarán primero en DEMO."
    )


# ============================================================
# COMANDO /senal
# ============================================================

async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Analizando el mercado...\n\n"
        "El modulo de analisis M1 continua en configuracion.\n"
        "Las senales se probarán primero en DEMO."
    )


# ============================================================
# COMANDO /resultado
# ============================================================

async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 REGISTRO DE RESULTADO\n\n"
        "Esta funcion quedará conectada al sistema "
        "de estadísticas del bot."
    )


# ============================================================
# COMANDO /estadisticas
# ============================================================

async def estadisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 ESTADISTICAS\n\n"
        "Todavia no hay operaciones registradas."
    )


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():

    # --------------------------------------------------------
    # Verificar TOKEN
    # --------------------------------------------------------

    if not TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN en las variables de entorno."
        )

    logger.info("Iniciando servidor web para Render...")

    # --------------------------------------------------------
    # Flask en segundo plano
    # --------------------------------------------------------

    web_thread = threading.Thread(
        target=iniciar_servidor_web,
        daemon=True
    )

    web_thread.start()

    logger.info(
        "Servidor web iniciado en el puerto %s",
        PORT
    )

    # --------------------------------------------------------
    # Crear aplicación de Telegram
    # --------------------------------------------------------

    telegram_app = Application.builder().token(TOKEN).build()

    # --------------------------------------------------------
    # Comandos de Telegram
    # --------------------------------------------------------

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("senal", senal)
    )

    telegram_app.add_handler(
        CommandHandler("señal", senal)
    )

    telegram_app.add_handler(
        CommandHandler("resultado", resultado)
    )

    telegram_app.add_handler(
        CommandHandler("estadisticas", estadisticas)
    )

    # --------------------------------------------------------
    # Información de inicio
    # --------------------------------------------------------

    logger.info("🤖 SENALES PRO M1 iniciado correctamente.")
    logger.info("Telegram Long Polling iniciado.")
    logger.info(
        "Servidor HTTP escuchando en puerto %s.",
        PORT
    )

    # --------------------------------------------------------
    # Telegram Long Polling
    # --------------------------------------------------------

    telegram_app.run_polling()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
