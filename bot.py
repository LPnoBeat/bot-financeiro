import pandas as pd
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === CONFIGURAÇÕES ===
TOKEN = "7992235959:AAH22o0RvrUUPHcKTVEoJbKPg8L2eDNf7N0"

# Link da planilha SharePoint (visualização pública)
EXCEL_URL = "https://microsoftcaldeira-my.sharepoint.com/:x:/g/personal/felipe_silva_microsoftcaldeira_onmicrosoft_com/EVfa7aGnfKtPlBeznuWt4ioB1FCMKh4vQwx5xUrETCbUJQ?e=gUfwWh"

# === FUNÇÃO PARA LER PLANILHA ONLINE ===
def ler_planilha_online():
    response = requests.get(EXCEL_URL)
    excel_data = BytesIO(response.content)
    df = pd.read_excel(excel_data)
    return df

# === COMANDOS ===

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = ler_planilha_online()
    if 'Saldo' in df.columns:
        total = df['Saldo'].sum()
        await update.message.reply_text(f"💰 Saldo total: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        await update.message.reply_text("❌ Coluna 'Saldo' não encontrada na planilha.")

async def extrato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = ler_planilha_online()
    if 'Data' in df.columns and 'Descrição' in df.columns and 'Valor' in df.columns:
        ultimos = df[['Data', 'Descrição', 'Valor']].tail(5)
        texto = "📄 Últimos 5 lançamentos:\n\n"
        for _, row in ultimos.iterrows():
            data = pd.to_datetime(row['Data']).strftime('%d/%m/%Y')
            texto += f"{data} - {row['Descrição']} - R$ {row['Valor']:,.2f}\n"
        await update.message.reply_text(texto.replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        await update.message.reply_text("❌ Colunas necessárias ('Data', 'Descrição', 'Valor') não encontradas.")

async def parcelas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = ler_planilha_online()
    if 'Parcela' in df.columns and 'Valor' in df.columns:
        agrupado = df.groupby('Parcela')['Valor'].sum()
        texto = "📌 Total por parcela:\n\n"
        for parcela, valor in agrupado.items():
            texto += f"{parcela}: R$ {valor:,.2f}\n"
        await update.message.reply_text(texto.replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        await update.message.reply_text("❌ Colunas 'Parcela' ou 'Valor' não encontradas.")

# === MAIN ===

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("extrato", extrato))
    app.add_handler(CommandHandler("parcelas", parcelas))

    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()