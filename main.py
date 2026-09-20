import os
import logging
import threading
import time
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters


# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
IQ_USERNAME = os.environ.get("IQ_USERNAME")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")

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
    return "SENALES PRO M1 - Bot activo", 200


@app.route("/health")
def health():
    return "OK", 200


def iniciar_servidor_web():
    logger.info("Iniciando servidor HTTP en 0.0.0.0:%s", PORT)

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
        threaded=True
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
        "/resultado - Registrar resultado de la operacion\n"
        "/estadisticas - Ver estadisticas de las operaciones\n\n"
        "Las senales se probaran primero en DEMO."
    )
# ============================================================
# DATOS EUR/USD M1 - TWELVE DATA
# ============================================================

def obtener_velas_eurusd():

    if not TWELVE_DATA_API_KEY:
        logger.error("Falta TWELVE_DATA_API_KEY.")
        return None

    url = "https://api.twelvedata.com/time_series"

    parametros = {
        "symbol": "EUR/USD",
        "interval": "1min",
        "outputsize": 20,
        "apikey": TWELVE_DATA_API_KEY
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            timeout=10
        )

        datos = respuesta.json()
logger.info("RESPUESTA TWELVE DATA: %s", datos)
        if "values" not in datos:
            logger.error("Error Twelve Data: %s", datos)
            return None

        return datos["values"]

    except Exception as e:
        logger.exception(
            "Error obteniendo EUR/USD M1: %s",
            e
        )
        return None

# ============================================================
# COMANDO /senal
# ============================================================

async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    velas = obtener_velas_eurusd()

    if not velas:
        await update.message.reply_text(
            "⚠️ No se pudieron obtener los datos de EUR/USD M1.\n\n"
            "Revisa la conexión con Twelve Data."
        )
        return

    ultima = velas[0]

    apertura = float(ultima["open"])
    cierre = float(ultima["close"])
    maximo = float(ultima["high"])
    minimo = float(ultima["low"])

    if cierre > apertura:
        direccion = "CALL 📈"
    elif cierre < apertura:
        direccion = "PUT 📉"
    else:
        direccion = "ESPERAR ⏸️"

    await update.message.reply_text(
        "📊 SENALES PRO M1\n\n"
        "💱 Par: EUR/USD\n"
        "⏱️ Temporalidad: 1 minuto\n"
        "🧪 Modo: DEMO\n\n"
        f"🕯️ Apertura: {apertura}\n"
        f"🕯️ Cierre: {cierre}\n"
        f"🔺 Máximo: {maximo}\n"
        f"🔻 Mínimo: {minimo}\n\n"
        f"📌 Lectura inicial: {direccion}\n\n"
        "⚠️ Esta es una lectura inicial de prueba."
    )

    
    
        


        
    

        
    
    
        
        

        
        
    


# ============================================================
# COMANDO /resultado
# ============================================================

async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 REGISTRO DE RESULTADO\n\n"
        "Esta funcion quedara conectada al sistema "
        "de estadisticas del bot."
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
# CREAR TELEGRAM
# ============================================================

def crear_bot():

    telegram_app = Application.builder().token(TOKEN).build()

    telegram_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_app.add_handler(
        CommandHandler("senal", senal)
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.Regex(r"(?i)^/?señal$"),
            senal
        )
    )

    telegram_app.add_handler(
        CommandHandler("resultado", resultado)
    )

    telegram_app.add_handler(
        CommandHandler("estadisticas", estadisticas)
    )

    return telegram_app


# ============================================================
# TELEGRAM
# ============================================================

def ejecutar_telegram():

    while True:

        try:
            logger.info("🤖 Iniciando Telegram Long Polling...")

            telegram_app = crear_bot()

            telegram_app.run_polling(
    drop_pending_updates=False,
    stop_signals=None
            )
    
    
            
        
            

            logger.warning(
                "Telegram Long Polling se detuvo. "
                "Reintentando en 5 segundos..."
            )

        except Exception as e:

            logger.exception(
                "Error en Telegram: %s",
                e
            )

        time.sleep(5)


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():

    if not TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN en las variables de entorno."
        )

    logger.info("========================================")
    logger.info("🤖 SENALES PRO M1")
    logger.info("Iniciando aplicacion...")
    logger.info("========================================")

    # --------------------------------------------------------
    # SERVIDOR HTTP PARA RENDER
    # --------------------------------------------------------

    web_thread = threading.Thread(
        target=iniciar_servidor_web,
        daemon=True
    )

    web_thread.start()

    logger.info(
        "Servidor HTTP iniciado. Puerto: %s",
        PORT
    )

    # --------------------------------------------------------
    # TELEGRAM
    # --------------------------------------------------------

    telegram_thread = threading.Thread(
        target=ejecutar_telegram,
        daemon=False
    )

    telegram_thread.start()

    logger.info("Telegram iniciado correctamente.")
    logger.info("Bot listo para recibir comandos.")

    # --------------------------------------------------------
    # MANTENER PROCESO VIVO
    # --------------------------------------------------------

    telegram_thread.join()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
