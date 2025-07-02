import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# TOKEN fornecido
TOKEN = "7992235959:AAH22o0RvrUUPHcKTVEoJbKPg8L2eDNf7N0"

# LINK da planilha SharePoint/OneDrive (export CSV)
SHEET_URL = "https://microsoftcaldeira-my.sharepoint.com/:x:/g/personal/felipe_silva_microsoftcaldeira_onmicrosoft_com/EVfa7aGnfKtPlBeznuWt4ioB1FCMKh4vQwx5xUrETCbUJQ?e=gUfwWh"

# converte link compartilhado em um que exporta CSV diretamente
def converter_para_csv_url(link):
    if "?" in link:
        link = link.split("?")[0]
    return f"{link}?web=1&action=download"

# Função para obter saldo da planilha (assumindo que a palavra 'Saldo' está na linha correspondente)
def get_saldo():
    csv_url = converter_para_csv_url(SHEET_URL)
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        linhas = response.text.splitlines()
        for linha in linhas:
            if "Saldo" in linha:
                partes = linha.split(",")
                if len(partes) > 1:
                    return partes[1]
        return "❌ Saldo não encontrado na planilha."
    except Exception as e:
        return f"⚠️ Erro ao buscar saldo: {str(e)}"

# Comando /saldo
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valor = get_saldo()
    await update.message.reply_text(f"💰 Seu saldo é: {valor}")

# Função principal
def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("saldo", saldo))
    app.run_polling()

if __name__ == "__main__":
    main()