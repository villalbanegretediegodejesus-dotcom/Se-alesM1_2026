import os
import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
# CONTROL DEL BOT
# ============================================================

BOT_ACTIVO = False
OPERACION_ACTIVA = False
CHAT_ID = None
async def encender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVO
    global CHAT_ID

    BOT_ACTIVO = True
    CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "🟢 BOT ENCENDIDO\n\n"
        "El bot queda activo para analizar el mercado "
        "automaticamente.\n"
        "💱 Par: EUR/USD\n"
        "⏱️ Temporalidad: M1\n"
        "🧪 Modo: DEMO"
    )
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
# COMANDO /encender
# ============================================================
async def encender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVO
    global CHAT_ID

    BOT_ACTIVO = True
    CHAT_ID = update.effective_chat.id

    await update.message.reply_text(
        "🟢 BOT ENCENDIDO\n\n"
        "El bot queda activo para analizar el mercado.\n"
        "Modo: DEMO"
    )
# ============================================================
# COMANDO /apagar
# ============================================================

async def apagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVO

    BOT_ACTIVO = False

    await update.message.reply_text(
        "🔴 BOT APAGADO\n\n"
        "El bot ya no generara senales.\n"
        "Puedes volver a encenderlo cuando quieras con /encender."
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
# ANALISIS AUTOMATICO M1
# ============================================================

async def analisis_automatico(context: ContextTypes.DEFAULT_TYPE):

    global BOT_ACTIVO
    global CHAT_ID

    if not BOT_ACTIVO:
        logger.info("ANALISIS AUTOMATICO OMITIDO: BOT_APAGADO")
        return

    if not CHAT_ID:
        logger.info("ANALISIS AUTOMATICO OMITIDO: CHAT_ID VACIO")
        return

    logger.info("ANALISIS AUTOMATICO INICIADO: BOT_ACTIVO=%s CHAT_ID=%s", BOT_ACTIVO, CHAT_ID)

    velas = obtener_velas_eurusd()

    if not velas or len(velas) < 10:
        logger.warning("No hay suficientes datos para analisis automatico.")
        return

    try:

        datos = []

        for vela in velas:

            datos.append({
                "datetime": vela["datetime"],
                "open": float(vela["open"]),
                "high": float(vela["high"]),
                "low": float(vela["low"]),
                "close": float(vela["close"])
            })

        ultimas_10 = datos[:10]

        velas_alcistas = 0
        velas_bajistas = 0

        for vela in ultimas_10:

            if vela["close"] > vela["open"]:
                velas_alcistas += 1

            elif vela["close"] < vela["open"]:
                velas_bajistas += 1

        precio_inicial = ultimas_10[-1]["open"]
        precio_actual = ultimas_10[0]["close"]

        if precio_actual > precio_inicial:
            tendencia = "ALCISTA 📈"

        elif precio_actual < precio_inicial:
            tendencia = "BAJISTA 📉"

        else:
            tendencia = "LATERAL ⏸️"

        soporte = min(
            vela["low"]
            for vela in ultimas_10
        )

        resistencia = max(
            vela["high"]
            for vela in ultimas_10
        )

        # ----------------------------------------------------
        # SOLO ENVIAR CUANDO EXISTE CONFIRMACION
        # ----------------------------------------------------
        if velas_alcistas > velas_bajistas:

            direccion = "CALL 📈"
            confirmacion = "Mayoría de velas alcistas."

        elif velas_bajistas > velas_alcistas:

            direccion = "PUT 📉"
            confirmacion = "Mayoría de velas bajistas."

        else:

            if tendencia == "ALCISTA 📈":

                direccion = "CALL 📈"
                confirmacion = "Velas equilibradas; se utiliza la tendencia general."

            else:

                direccion = "PUT 📉"
                confirmacion = "Velas equilibradas; se utiliza la tendencia general."

        # ----------------------------------------------------
        # ENVIAR SENAL AUTOMATICA
        # ----------------------------------------------------
                # HORA DE ENTRADA EN COLOMBIA
        ahora_colombia = datetime.now(ZoneInfo("America/Bogota"))
        hora_entrada = ahora_colombia + timedelta(minutes=1)
        hora_entrada_texto = hora_entrada.strftime("%H:%M")
        
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=(
                "🤖 SENALES PRO M1 - AUTOMATICA\n\n"
                "💱 Par: EUR/USD\n"
                "⏱️ Temporalidad: 1 minuto\n"
                "🧪 Modo: DEMO\n\n"
                f"📈 Velas alcistas: {velas_alcistas}\n"
                f"📉 Velas bajistas: {velas_bajistas}\n"
                f"📊 Tendencia: {tendencia}\n\n"
                f"🧱 Soporte: {soporte}\n"
                f"🧱 Resistencia: {resistencia}\n\n"
                f"📌 SENAL: {direccion}\n"
                f"🕐 HORA DE ENTRADA: {hora_entrada_texto}\n"
                f"⏱️ Duracion: 1 minuto\n"
                f"🔎 Confirmacion: {confirmacion}\n\n"
                "⚠️ Analisis M1 en fase DEMO."
            )
        )

        logger.info(
            "SENAL AUTOMATICA ENVIADA: %s",
            direccion
        )

    except Exception as e:

        logger.exception(
            "Error en analisis automatico M1: %s",
            e
        )
        
        

    
    

    
    
        
        
            
        

                
    
        

        

    

        

            
        


# ============================================================
# COMANDO /senal
# ============================================================

async def senal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not BOT_ACTIVO:
        await update.message.reply_text(
            "🔴 BOT APAGADO\n\n"
            "El bot no esta generando senales.\n"
            "Usa /encender cuando quieras comenzar."
        )
        return

    velas = obtener_velas_eurusd()

    if not velas or len(velas) < 10:
        await update.message.reply_text(
            "⚠️ No hay suficientes datos para analizar EUR/USD M1."
        )
        return

    try:

        # ----------------------------------------------------
        # CONVERTIR DATOS
        # ----------------------------------------------------

        datos = []

        for vela in velas:

            datos.append({
                "datetime": vela["datetime"],
                "open": float(vela["open"]),
                "high": float(vela["high"]),
                "low": float(vela["low"]),
                "close": float(vela["close"])
            })

        # ----------------------------------------------------
        # ULTIMA VELA
        # ----------------------------------------------------

        ultima = datos[0]

        apertura = ultima["open"]
        cierre = ultima["close"]
        maximo = ultima["high"]
        minimo = ultima["low"]

        # ----------------------------------------------------
        # ANALISIS DE LAS ULTIMAS 10 VELAS
        # ----------------------------------------------------

        ultimas_10 = datos[:10]

        velas_alcistas = 0
        velas_bajistas = 0

        for vela in ultimas_10:

            if vela["close"] > vela["open"]:
                velas_alcistas += 1

            elif vela["close"] < vela["open"]:
                velas_bajistas += 1

        # ----------------------------------------------------
        # MOVIMIENTO GENERAL
        # ----------------------------------------------------

        precio_inicial = ultimas_10[-1]["open"]
        precio_actual = ultimas_10[0]["close"]

        if precio_actual > precio_inicial:
            tendencia = "ALCISTA 📈"

        elif precio_actual < precio_inicial:
            tendencia = "BAJISTA 📉"

        else:
            tendencia = "LATERAL ⏸️"

        # ----------------------------------------------------
        # SOPORTE Y RESISTENCIA RECIENTES
        # ----------------------------------------------------

        soporte = min(
            vela["low"]
            for vela in ultimas_10
        )

        resistencia = max(
            vela["high"]
            for vela in ultimas_10
        )

        # ----------------------------------------------------
        # DECISION INICIAL
        # ----------------------------------------------------

        if velas_alcistas >= 6 and tendencia == "ALCISTA 📈":

            direccion = "CALL 📈"
            confirmacion = "Tendencia alcista con mayoria de velas positivas."

        elif velas_bajistas >= 6 and tendencia == "BAJISTA 📉":

            direccion = "PUT 📉"
            confirmacion = "Tendencia bajista con mayoria de velas negativas."

        else:

            direccion = "ESPERAR ⏸️"
            confirmacion = "No existe suficiente confirmacion."

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        await update.message.reply_text(
            "📊 SENALES PRO M1\n\n"
            "💱 Par: EUR/USD\n"
            "⏱️ Temporalidad: 1 minuto\n"
            "🧪 Modo: DEMO\n\n"

            f"🕯️ Apertura: {apertura}\n"
            f"🕯️ Cierre: {cierre}\n"
            f"🔺 Maximo: {maximo}\n"
            f"🔻 Minimo: {minimo}\n\n"

            f"📈 Velas alcistas: {velas_alcistas}\n"
            f"📉 Velas bajistas: {velas_bajistas}\n"
            f"📊 Tendencia: {tendencia}\n\n"

            f"🧱 Soporte: {soporte}\n"
            f"🧱 Resistencia: {resistencia}\n\n"

            f"📌 Senal: {direccion}\n"
            f"🔎 Confirmacion: {confirmacion}\n\n"

            "⚠️ Analisis M1 en fase DEMO."
        )

    except Exception as e:

        logger.exception(
            "Error en el analisis M1: %s",
            e
        )

        await update.message.reply_text(
            "⚠️ Ocurrio un error durante el analisis M1."
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
        CommandHandler("encender", encender)
    )

    telegram_app.add_handler(
        CommandHandler("apagar", apagar)
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
    # ========================================================
    # ANALISIS AUTOMATICO CADA 1 MINUTO
    # ========================================================

    telegram_app.job_queue.run_repeating(
    analisis_automatico,
    interval=300,
    first=10
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
