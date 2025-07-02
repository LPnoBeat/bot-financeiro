import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

ARQUIVO_PLANILHA = "Controle_Financeiro.xlsx"

def identificar_destino(tipo, categoria):
    tipo = tipo.lower()
    categoria = categoria.lower()
    if categoria in ["salario", "salário", "recebido", "salário_recebido"]:
        categoria = "salário"
    elif categoria in ["alimentação", "alimentacao"]:
        categoria = "alimentação"
    elif categoria in ["cartão", "cartao", "carregado", "cartão_raiô", "cartao_raiô"]:
        categoria = "cartão"
    if tipo == "entrada":
        if categoria in ["alimentação", "cartão"]:
            return "Entradas Raiô"
        elif categoria == "salário":
            return "Salário"
    elif tipo == "gasto":
        if categoria == "alimentação":
            return "Gastos Raiô"
        else:
            return "Gastos Salário"
    return None

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text.strip()
        if texto.lower().startswith("conta paga"):
            await registrar_conta_paga(update, context)
            return
        partes = texto.split()
        if len(partes) < 3:
            await update.message.reply_text("⚠️ Formato inválido. Use: Entrada/Gasto Categoria Valor")
            return
        tipo = partes[0].lower()
        categoria = partes[1]
        valor_str = partes[2].replace(",", ".")
        valor = float(valor_str)
        agora = datetime.now().strftime("%d/%m/%Y")
        aba = identificar_destino(tipo, categoria)
        if not aba:
            await update.message.reply_text("❌ Categoria ou tipo não reconhecido.")
            return
        df = pd.read_excel(ARQUIVO_PLANILHA, sheet_name=aba)
        if aba in ["Entradas Raiô", "Salário"]:
            nova_linha = pd.DataFrame([{"Data": agora, "Fonte": categoria, "Valor": valor}])
        else:
            nova_linha = pd.DataFrame([{"Data": agora, "Descrição": categoria, "Categoria": categoria, "Valor": valor}])
        df = pd.concat([df, nova_linha], ignore_index=True)
        with pd.ExcelWriter(ARQUIVO_PLANILHA, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=aba, index=False)
        await update.message.reply_text(f"✅ Registrado em *{aba}*: {categoria} R$ {valor:.2f}", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao processar: {e}")

async def comando_resumo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        def soma_aba(aba):
            try:
                df = pd.read_excel(ARQUIVO_PLANILHA, sheet_name=aba)
                return df["Valor"].sum()
            except:
                return 0.0
        entradas_raio = soma_aba("Entradas Raiô")
        gastos_raio = soma_aba("Gastos Raiô")
        entradas_salario = soma_aba("Salário")
        gastos_salario = soma_aba("Gastos Salário")
        disponivel_raio = entradas_raio - gastos_raio
        disponivel_salario = entradas_salario - gastos_salario
        resposta = (
            f"💳 *Raiô*\n"
            f"Entrou: R$ {entradas_raio:.2f}\n"
            f"Disponível: R$ {disponivel_raio:.2f}\n\n"
            f"💼 *Salário*\n"
            f"Entrou: R$ {entradas_salario:.2f}\n"
            f"Disponível: R$ {disponivel_salario:.2f}"
        )
        await update.message.reply_text(resposta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro no resumo: {e}")

async def comando_contas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        df_pagar = pd.read_excel(ARQUIVO_PLANILHA, sheet_name="Contas a pagar")
        df_pagas = pd.read_excel(ARQUIVO_PLANILHA, sheet_name="Contas Pagas")
        contas_pagas = set(df_pagas["Descrição"].str.lower())
        resposta = "*📋 Contas a Pagar:*\n"
        for _, row in df_pagar.iterrows():
            descricao = row["Descrição"]
            valor = row["Valor"]
            if descricao.lower() in contas_pagas:
                resposta += f"✅ {descricao}: R$ {valor:.2f}\n"
            else:
                resposta += f"❌ {descricao}: R$ {valor:.2f}\n"
        await update.message.reply_text(resposta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao ler as contas: {e}")

async def registrar_conta_paga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text.strip()
        partes = texto.split()
        if len(partes) < 4:
            await update.message.reply_text("⚠️ Formato inválido. Use: Conta paga <Descrição> <Valor>")
            return
        descricao = " ".join(partes[2:-1])
        valor_str = partes[-1].replace(",", ".")
        valor = float(valor_str)
        data = datetime.now().strftime("%d/%m/%Y")
        nova_linha = pd.DataFrame([{"Descrição": descricao, "Valor": valor, "Data": data}])
        df_existente = pd.read_excel(ARQUIVO_PLANILHA, sheet_name="Contas Pagas")
        df_novo = pd.concat([df_existente, nova_linha], ignore_index=True)
        with pd.ExcelWriter(ARQUIVO_PLANILHA, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_novo.to_excel(writer, sheet_name="Contas Pagas", index=False)
        await update.message.reply_text(f"✅ Conta paga registrada: {descricao.title()} - R$ {valor:.2f}")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao registrar conta paga: {e}")

def main():
    app = ApplicationBuilder().token("7992235959:AAH22o0RvrUUPHcKTVEoJbKPg8L2eDNf7N0").build()
    app.add_handler(CommandHandler("resumo", comando_resumo))
    app.add_handler(CommandHandler("contas", comando_contas))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem))
    app.run_polling()

if __name__ == '__main__':
    main()
