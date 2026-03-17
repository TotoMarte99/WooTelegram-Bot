import requests #Se utiliza para enviar peticiones HTTP a WooCommerce
import os 
from dotenv import load_dotenv
from telegram import Update  #Update es para representar los mensajes que llegan al bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)

# Configuracion de la api de woocommerce y del bot en telegram.

load_dotenv()
TOKEN = os.getenv("TOKEN")
WC_API = os.getenv("WC_API")
WC_KEY = os.getenv("WC_KEY")
WC_SECRET = os.getenv("WC_SECRET")
# Estados de la conversacion, se crean 5 estados para saber la parte de la conversacion.
NOMBRE, PRECIO, STOCK, DESCRIPCION, CATEGORIA, FOTOS = range(6)


#Funciones para Telegram
async def nuevo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Nombre del producto:")
    return NOMBRE

async def nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text
    await update.message.reply_text("Precio:")
    return PRECIO


async def precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["precio"] = update.message.text
    await update.message.reply_text("Stock:")
    return STOCK


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stock"] = update.message.text
    await update.message.reply_text("Descripción:")
    return DESCRIPCION


async def descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["descripcion"] = update.message.text
    await update.message.reply_text("Categoría del producto:")
    return CATEGORIA

async def categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["categoria"] = update.message.text
    context.user_data["imagenes"] = []

    await update.message.reply_text(
        "Envia las imagenes del producto (una por una). Cuando terminess escribi /fin"
    )

    return FOTOS

async def fotos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    context.user_data["imagenes"].append({
        "src": file.file_path
    })

    await update.message.reply_text("Imagen agregada. Envia otra o escribi /fin")

async def fin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Procesando producto...")

    data = {
        "name": context.user_data["nombre"],
        "type": "simple",
        "regular_price": context.user_data["precio"],
        "description": context.user_data["descripcion"],
        "manage_stock": True,
        "stock_quantity": int(context.user_data["stock"]),
        "categories": [
            {"name": context.user_data["categoria"]}
        ],
        "images": context.user_data["imagenes"]
    }

    r = requests.post(
        f"{WC_API}/products",
        auth=(WC_KEY, WC_SECRET),
        json=data
    )

    print(r.text)

    producto = r.json()

    await update.message.reply_text(
        f"Producto creado ID: {producto['id']}"
    )

    return ConversationHandler.END


async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    photo = update.message.photo[-1]
    file = await photo.get_file()
    url_imagen = file.file_path

    data = {
        "name": context.user_data["nombre"],
        "type": "simple",
        "regular_price": context.user_data["precio"],
        "description": context.user_data["descripcion"],
        "manage_stock": True,
        "stock_quantity": int(context.user_data["stock"]),
        "images": [
            {"src": url_imagen}
        ]
    }

    r = requests.post(
        f"{WC_API}/products",
        auth=(WC_KEY, WC_SECRET),
        json=data
    )

    producto = r.json()

    await update.message.reply_text(
        f"Producto creado\n"
        f"ID: {producto['id']}\n"
        f"Nombre: {producto['name']}"
    )

    return ConversationHandler.END


app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("nuevo", nuevo)],
    states={
        NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nombre)],
        PRECIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, precio)],
        STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, stock)],
        DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, descripcion)],
        CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, categoria)],

        FOTOS: [
            MessageHandler(filters.PHOTO, fotos),
            CommandHandler("fin", fin)
        ]
    },
    fallbacks=[]
)

app.add_handler(conv)

print("Bot iniciado...")

app.run_polling()
