# sistema_imobiliaria.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import urllib.parse
import re
import gspread

st.set_page_config(page_title="Sistema Imobiliário", layout="wide", page_icon="🏢")

# ==================== CONFIGURAÇÃO DO GOOGLE SHEETS ====================
ID_PLANILHA = "1-i2GpqDZPC6l0jGn4a5f5odOqP4UhHkYKGb6y1UzQUE"
ABA_LEADS = "leads"
ABA_MENSAGENS = "mensagens"
ABA_AGENDA = "agenda"
ABA_IMOVEIS = "imoveis"

def conectar_google_sheets():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        client = gspread.service_account_from_dict(creds_dict)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None

def abrir_planilha(client):
    return client.open_by_key(ID_PLANILHA)

def garantir_aba(planilha, nome_aba, rows="1000", cols="20"):
    try:
        return planilha.worksheet(nome_aba)
    except Exception:
        return planilha.add_worksheet(title=nome_aba, rows=rows, cols=cols)

# ==================== FUNÇÕES PARA LEADS ====================
def carregar_leads():
    client = conectar_google_sheets()
    if not client:
        return []
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_LEADS)
        if aba.row_count == 0 or not aba.get_all_values():
            cabecalho = ["ID", "Nome", "Telefone", "Data Cadastro", "Perfil", "Código Imóvel",
                         "Link Imóvel", "Valor", "Origem", "Status", "Último Contato", "Observações",
                         "Quartos Desejados", "Banheiros Desejados", "Vagas Desejadas", "Metragem Desejada", "Bairro Desejado"]
            aba.append_row(cabecalho)
        dados = aba.get_all_records()
        leads = []
        for i, row in enumerate(dados):
            if i == 0 and row.get("ID") == "ID":
                continue
            def to_int(val):
                if val is None or str(val).strip() == "":
                    return 0
                try:
                    return int(val)
                except:
                    return 0
            def to_float(val):
                if val is None or str(val).strip() == "":
                    return 0.0
                try:
                    return float(val)
                except:
                    return 0.0
            leads.append({
                "id": int(row.get("ID", i+1)),
                "nome": str(row.get("Nome", "")),
                "telefone": str(row.get("Telefone", "")),
                "data_cadastro": str(row.get("Data Cadastro", "")),
                "perfil": str(row.get("Perfil", "primeira_compra")),
                "codigo_imovel": str(row.get("Código Imóvel", "")),
                "link_imovel": str(row.get("Link Imóvel", "")),
                "valor_imovel": str(row.get("Valor", "")),
                "origem": str(row.get("Origem", "")),
                "status": str(row.get("Status", "novo")),
                "ultimo_contato": str(row.get("Último Contato", "")),
                "observacoes": str(row.get("Observações", "")),
                "quartos_desejados": to_int(row.get("Quartos Desejados")),
                "banheiros_desejados": to_int(row.get("Banheiros Desejados")),
                "vagas_desejadas": to_int(row.get("Vagas Desejadas")),
                "metragem_desejada": to_float(row.get("Metragem Desejada")),
                "bairro_desejado": str(row.get("Bairro Desejado", "")),
                "mensagens_enviadas": []
            })
        return leads
    except Exception as e:
        st.error(f"Erro ao carregar leads: {e}")
        return []

def salvar_leads(leads):
    client = conectar_google_sheets()
    if not client:
        return False
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_LEADS)
        cabecalho = ["ID", "Nome", "Telefone", "Data Cadastro", "Perfil", "Código Imóvel",
                     "Link Imóvel", "Valor", "Origem", "Status", "Último Contato", "Observações",
                     "Quartos Desejados", "Banheiros Desejados", "Vagas Desejadas", "Metragem Desejada", "Bairro Desejado"]
        dados = []
        for lead in leads:
            dados.append([
                lead.get("id", ""),
                lead.get("nome", ""),
                lead.get("telefone", ""),
                lead.get("data_cadastro", ""),
                lead.get("perfil", ""),
                lead.get("codigo_imovel", ""),
                lead.get("link_imovel", ""),
                lead.get("valor_imovel", ""),
                lead.get("origem", ""),
                lead.get("status", ""),
                lead.get("ultimo_contato", ""),
                lead.get("observacoes", ""),
                lead.get("quartos_desejados", 0),
                lead.get("banheiros_desejados", 0),
                lead.get("vagas_desejadas", 0),
                lead.get("metragem_desejada", 0.0),
                lead.get("bairro_desejado", "")
            ])
        aba.clear()
        aba.append_row(cabecalho)
        if dados:
            aba.append_rows(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar leads: {e}")
        return False

# ==================== FUNÇÕES PARA MENSAGENS ====================
def carregar_mensagens():
    client = conectar_google_sheets()
    if not client:
        return []
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_MENSAGENS, rows="100", cols="10")
        if not aba.get_all_values():
            cabecalho = ["ID", "Título", "Categoria", "Mensagem", "Ativa"]
            aba.append_row(cabecalho)
            dados_padrao = [
                [1, "🔥 Sextou - Leads Quentes", "sexta", "Olá {nome}! 🎉✨\n\nSEXTOU! Sobre o imóvel {codigo} no valor de {valor}, ainda está disponível! 🏠\n\nBora dar uma olhada? 😊", True],
                [2, "🌡️ Acompanhamento", "acompanhamento", "Olá {nome}! 👋😊\n\nFaz um tempo que não falamos sobre o imóvel {codigo} no valor de {valor}...\n\nAinda está interessado? 😄", True],
                [3, "❄️ Reativação", "reativacao", "Olá {nome}! 🙌😊\n\nLembrei de você! Ainda tem interesse no imóvel {codigo}? Apareceu outras opções! 🏠\n\nQual a boa? 💬", True]
            ]
            aba.append_rows(dados_padrao)
        dados = aba.get_all_records()
        mensagens = []
        for row in dados:
            if row.get("ID"):
                mensagens.append({
                    "id": row.get("ID"),
                    "titulo": str(row.get("Título", "")),
                    "categoria": str(row.get("Categoria", "")),
                    "mensagem": str(row.get("Mensagem", "")),
                    "ativa": str(row.get("Ativa", True)).lower() in ("true", "1", "sim")
                })
        return mensagens
    except Exception as e:
        st.error(f"Erro ao carregar mensagens: {e}")
        return []

def salvar_mensagens(mensagens):
    client = conectar_google_sheets()
    if not client:
        return False
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_MENSAGENS, rows="100", cols="10")
        cabecalho = ["ID", "Título", "Categoria", "Mensagem", "Ativa"]
        dados = []
        for m in mensagens:
            dados.append([
                m.get("id", ""),
                m.get("titulo", ""),
                m.get("categoria", ""),
                m.get("mensagem", ""),
                m.get("ativa", True)
            ])
        aba.clear()
        aba.append_row(cabecalho)
        if dados:
            aba.append_rows(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar mensagens: {e}")
        return False

# ==================== FUNÇÕES PARA AGENDA ====================
def carregar_compromissos():
    client = conectar_google_sheets()
    if not client:
        return []
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_AGENDA, rows="100", cols="10")
        if not aba.get_all_values():
            cabecalho = ["ID", "Título", "Tipo", "Data", "Horário", "Lead Nome", "Observações", "Criado em"]
            aba.append_row(cabecalho)
        dados = aba.get_all_records()
        compromissos = []
        for row in dados:
            if row.get("ID"):
                compromissos.append({
                    "id": row.get("ID"),
                    "titulo": str(row.get("Título", "")),
                    "tipo": str(row.get("Tipo", "")),
                    "data": str(row.get("Data", "")),
                    "horario": str(row.get("Horário", "")),
                    "lead_nome": str(row.get("Lead Nome", "")),
                    "observacoes": str(row.get("Observações", "")),
                    "criado_em": str(row.get("Criado em", ""))
                })
        return compromissos
    except Exception as e:
        st.error(f"Erro ao carregar compromissos: {e}")
        return []

def salvar_compromissos(compromissos):
    client = conectar_google_sheets()
    if not client:
        return False
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_AGENDA, rows="100", cols="10")
        cabecalho = ["ID", "Título", "Tipo", "Data", "Horário", "Lead Nome", "Observações", "Criado em"]
        dados = []
        for c in compromissos:
            dados.append([
                c.get("id", ""),
                c.get("titulo", ""),
                c.get("tipo", ""),
                c.get("data", ""),
                c.get("horario", ""),
                c.get("lead_nome", ""),
                c.get("observacoes", ""),
                c.get("criado_em", "")
            ])
        aba.clear()
        aba.append_row(cabecalho)
        if dados:
            aba.append_rows(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar compromissos: {e}")
        return False

def get_compromissos_do_dia(compromissos, data):
    return [c for c in compromissos if c.get("data") == data]

def get_compromissos_hoje(compromissos):
    hoje = datetime.now().strftime("%d/%m/%Y")
    return [c for c in compromissos if c.get("data") == hoje]

def mostrar_alerta_compromissos():
    if "compromissos" in st.session_state:
        hoje = datetime.now().strftime("%d/%m/%Y")
        compromissos_hoje = [c for c in st.session_state.compromissos if c.get("data") == hoje]
        if compromissos_hoje:
            st.warning(f"⚠️ **Você tem {len(compromissos_hoje)} compromisso(s) HOJE!**")
            for comp in compromissos_hoje:
                st.info(f"📅 **{comp['titulo']}** - {comp['horario']} - {comp.get('lead_nome', 'Sem lead')}")
            st.markdown("---")

# ==================== FUNÇÕES PARA IMÓVEIS ====================
def carregar_imoveis():
    client = conectar_google_sheets()
    if not client:
        return []
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_IMOVEIS)
        if aba.row_count == 0 or not aba.get_all_values():
            cabecalho = ["ID", "Código", "Valor", "Quartos", "Banheiros", "Vagas", "Metragem", "Bairro", "Rua", "Link", "Opcionista"]
            aba.append_row(cabecalho)
        dados = aba.get_all_records()
        imoveis = []
        for row in dados:
            if row.get("ID"):
                imoveis.append({
                    "id": row.get("ID"),
                    "codigo": str(row.get("Código", "")),
                    "valor": str(row.get("Valor", "")),
                    "quartos": row.get("Quartos", 0),
                    "banheiros": row.get("Banheiros", 0),
                    "vagas": row.get("Vagas", 0),
                    "metragem": row.get("Metragem", 0.0),
                    "bairro": str(row.get("Bairro", "")),
                    "rua": str(row.get("Rua", "")),
                    "link": str(row.get("Link", "")),
                    "opcionista": str(row.get("Opcionista", ""))
                })
        return imoveis
    except Exception as e:
        st.error(f"Erro ao carregar imóveis: {e}")
        return []

def salvar_imoveis(imoveis):
    client = conectar_google_sheets()
    if not client:
        return False
    try:
        planilha = abrir_planilha(client)
        aba = garantir_aba(planilha, ABA_IMOVEIS)
        cabecalho = ["ID", "Código", "Valor", "Quartos", "Banheiros", "Vagas", "Metragem", "Bairro", "Rua", "Link", "Opcionista"]
        dados = []
        for imv in imoveis:
            dados.append([
                imv.get("id", ""),
                imv.get("codigo", ""),
                imv.get("valor", ""),
                imv.get("quartos", 0),
                imv.get("banheiros", 0),
                imv.get("vagas", 0),
                imv.get("metragem", 0.0),
                imv.get("bairro", ""),
                imv.get("rua", ""),
                imv.get("link", ""),
                imv.get("opcionista", "")
            ])
        aba.clear()
        aba.append_row(cabecalho)
        if dados:
            aba.append_rows(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar imóveis: {e}")
        return False

def converter_valor_para_numero(valor_str):
    if not valor_str:
        return 0
    valor_str = str(valor_str).lower().strip()
    if valor_str.endswith('k'):
        return float(valor_str[:-1]) * 1000
    elif valor_str.endswith('m'):
        return float(valor_str[:-1]) * 1_000_000
    else:
        try:
            return float(valor_str)
        except:
            return 0

def recomendar_imoveis(lead, imoveis, tolerancia_valor=0.15, tolerancia_metragem=0.10):
    if not imoveis:
        return []
    valor_lead_num = converter_valor_para_numero(lead.get("valor_imovel", ""))
    if valor_lead_num == 0:
        return []
    min_valor = valor_lead_num * (1 - tolerancia_valor)
    max_valor = valor_lead_num * (1 + tolerancia_valor)
    recomendados = []
    for imv in imoveis:
        valor_imv_num = converter_valor_para_numero(imv.get("valor", ""))
        if valor_imv_num < min_valor or valor_imv_num > max_valor:
            continue
        qtd_desejada = lead.get("quartos_desejados")
        if qtd_desejada and imv.get("quartos") and int(imv.get("quartos")) != int(qtd_desejada):
            continue
        ban_desejado = lead.get("banheiros_desejados")
        if ban_desejado and imv.get("banheiros") and int(imv.get("banheiros")) != int(ban_desejado):
            continue
        vagas_desejadas = lead.get("vagas_desejadas")
        if vagas_desejadas and imv.get("vagas") and int(imv.get("vagas")) != int(vagas_desejadas):
            continue
        metragem_desejada = lead.get("metragem_desejada")
        if metragem_desejada and imv.get("metragem"):
            min_metragem = metragem_desejada * (1 - tolerancia_metragem)
            max_metragem = metragem_desejada * (1 + tolerancia_metragem)
            if float(imv.get("metragem")) < min_metragem or float(imv.get("metragem")) > max_metragem:
                continue
        bairro_desejado = lead.get("bairro_desejado", "").strip().lower()
        if bairro_desejado and bairro_desejado not in imv.get("bairro", "").lower():
            continue
        recomendados.append(imv)
    return recomendados

# ==================== CONFIGURAÇÕES ====================
PERFIS = {
    "primeira_compra": {"titulo": "🏠 Primeira Compra", "emoji": "🏠"},
    "investidor": {"titulo": "💰 Investidor", "emoji": "💰"},
    "upgrade": {"titulo": "✨ Upgrade", "emoji": "✨"},
    "luxo": {"titulo": "🌟 Luxo", "emoji": "🌟"}
}

VALORES_IMOVEL = [
    "450k", "500k", "550k", "600k", "650k", "700k", "750k", "800k",
    "850k", "900k", "950k", "1M", "1.2M", "1.3M", "1.4M", "1.5M",
    "1.7M", "1.8M", "2M", "2.5M", "3M", "3.5M"
]

ORIGENS = ["lead", "vitrine", "avulso", "captação", "avaliacao"]
STATUS_LISTA = ["novo", "em_andamento", "quente", "frio", "convertido", "perdido"]

# ==================== FUNÇÕES AUXILIARES ====================
def gerar_mensagem_ia(lead, temperatura):
    nome = lead.get("nome", "cliente").split()[0]
    perfil = lead.get("perfil", "primeira_compra")
    codigo = lead.get("codigo_imovel", "")
    valor = lead.get("valor_imovel", "")
    link = lead.get("link_imovel", "")
    if temperatura == "quente":
        if perfil == "investidor":
            return f"""Olá {nome}! 😎💰

Tudo certo? Sobre o imóvel {codigo} no valor de {valor}, é uma oportunidade MUITO boa pra investir!

💰 Rentabilidade acima da média
📍 Localização premium
🎯 Entrada facilitada

Quer dar uma olhada? {link if link else 'Me avisa aí!'} 😊"""
        elif perfil == "primeira_compra":
            return f"""Olá {nome}! 🏠✨

Sobre o imóvel {codigo} no valor de {valor}, ele é perfeito para você!

📌 Financiamento top demais
📌 Localização privilegiada

Bora agendar uma visita? 😊"""
        else:
            return f"""Olá {nome}! 🏡✨

O imóvel {codigo} no valor de {valor} é uma oportunidade única!

Bora dar uma olhada? {link if link else '😉💪'}"""
    elif temperatura == "morno":
        return f"""Olá {nome}! 👋😊

Faz um tempinho que não falamos sobre o imóvel {codigo}...

Surgiram novidades no mercado! Que tal dar uma conferida? {link if link else '😄'}"""
    else:
        return f"""Olá {nome}! 🙌😊

Lembrei de você! Ainda tem interesse no imóvel {codigo}? Apareceu outras opções!

Qual a boa? Me conta aí! {link if link else '💬😊'}"""

def calcular_temperatura(lead):
    if not lead.get("ultimo_contato"):
        return "novo"
    try:
        ultimo = datetime.strptime(lead["ultimo_contato"], "%d/%m/%Y")
        dias = (datetime.now() - ultimo).days
        if dias <= 3:
            return "quente"
        elif dias <= 10:
            return "morno"
        else:
            return "frio"
    except Exception:
        return "novo"

def formatar_telefone(telefone, link=False):
    telefone = str(telefone)
    telefone_formatado = re.sub(r"\D", "", telefone)
    if link:
        return f"https://wa.me/{telefone_formatado}"
    return telefone_formatado

def analisar_metricas(leads):
    if not leads:
        return None
    total = len(leads)
    convertidos = sum(1 for l in leads if l.get("status") == "convertido")
    taxa = (convertidos / total * 100) if total > 0 else 0
    conversao_perfil = {}
    for perfil in PERFIS.keys():
        leads_perfil = [l for l in leads if l.get("perfil") == perfil]
        if leads_perfil:
            conv = sum(1 for l in leads_perfil if l.get("status") == "convertido")
            conversao_perfil[perfil] = (conv / len(leads_perfil) * 100)
        else:
            conversao_perfil[perfil] = 0
    return {
        "taxa_conversao": taxa,
        "total_leads": total,
        "convertidos": convertidos,
        "conversao_por_perfil": conversao_perfil
    }

def verificar_sexta():
    return datetime.now().weekday() == 4

# ==================== INTERFACE PRINCIPAL ====================
def main():
    st.title("🏢 Sistema Inteligente de Acompanhamento de Leads")
    st.markdown("### 🤖 Com IA para ajudar na conversão de vendas")
    st.markdown("---")

    mostrar_alerta_compromissos()

    if verificar_sexta():
        st.success("🎉 **SEXTOU!** Hoje é dia de enviar mensagens para os leads! 🎉")
        st.balloons()

    # Carregar todos os dados
    if "leads" not in st.session_state:
        st.session_state.leads = carregar_leads()
    if "mensagens_personalizadas" not in st.session_state:
        st.session_state.mensagens_personalizadas = carregar_mensagens()
    if "compromissos" not in st.session_state:
        st.session_state.compromissos = carregar_compromissos()
    if "imoveis" not in st.session_state:
        st.session_state.imoveis = carregar_imoveis()

    metricas = analisar_metricas(st.session_state.leads)

    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.header("📝 Cadastro / Edição")

        if st.session_state.leads:
            nomes_leads = [l["nome"] for l in st.session_state.leads]
            lead_para_editar = st.selectbox("Selecione um lead:", ["➕ Novo Lead"] + nomes_leads)
        else:
            lead_para_editar = "➕ Novo Lead"
        st.markdown("---")

        # Reset automático quando "➕ Novo Lead" é selecionado
        if lead_para_editar == "➕ Novo Lead":
            nome_val = ""
            telefone_val = ""
            perfil_val = list(PERFIS.keys())[0]
            codigo_val = ""
            link_val = ""
            valor_val = VALORES_IMOVEL[0]
            origem_val = ORIGENS[0]
            status_val = STATUS_LISTA[0]
            quartos_desejados_val = 0
            banheiros_desejados_val = 0
            vagas_desejadas_val = 0
            metragem_desejada_val = 0.0
            bairro_desejado_val = ""
            observacoes_val = ""
            lead_edit = None
        else:
            lead_edit = next((l for l in st.session_state.leads if l["nome"] == lead_para_editar), None)
            if lead_edit:
                nome_val = lead_edit["nome"]
                telefone_val = lead_edit["telefone"]
                perfil_val = lead_edit["perfil"]
                codigo_val = lead_edit.get("codigo_imovel", "")
                link_val = lead_edit.get("link_imovel", "")
                valor_val = lead_edit.get("valor_imovel", VALORES_IMOVEL[0])
                origem_val = lead_edit.get("origem", ORIGENS[0])
                status_val = lead_edit.get("status", STATUS_LISTA[0])
                quartos_desejados_val = lead_edit.get("quartos_desejados", 0)
                banheiros_desejados_val = lead_edit.get("banheiros_desejados", 0)
                vagas_desejadas_val = lead_edit.get("vagas_desejadas", 0)
                metragem_desejada_val = lead_edit.get("metragem_desejada", 0.0)
                bairro_desejado_val = lead_edit.get("bairro_desejado", "")
                observacoes_val = lead_edit.get("observacoes", "")
            else:
                nome_val = ""
                telefone_val = ""
                perfil_val = list(PERFIS.keys())[0]
                codigo_val = ""
                link_val = ""
                valor_val = VALORES_IMOVEL[0]
                origem_val = ORIGENS[0]
                status_val = STATUS_LISTA[0]
                quartos_desejados_val = 0
                banheiros_desejados_val = 0
                vagas_desejadas_val = 0
                metragem_desejada_val = 0.0
                bairro_desejado_val = ""
                observacoes_val = ""
                lead_edit = None

        if lead_edit:
            st.info(f"✏️ Editando: {lead_edit['nome']}")
        else:
            st.info("➕ Cadastrar novo lead")

        nome = st.text_input("Nome do Cliente", value=nome_val)
        telefone = st.text_input("Telefone (apenas números)", value=telefone_val)

        perfil_index = list(PERFIS.keys()).index(perfil_val) if perfil_val in PERFIS else 0
        perfil = st.selectbox("Perfil", list(PERFIS.keys()), index=perfil_index, format_func=lambda x: PERFIS[x]["titulo"])

        st.markdown("### 🏠 Informações do Imóvel")
        codigo_imovel = st.text_input("Código do Imóvel", value=codigo_val)
        link_imovel = st.text_input("Link do Imóvel", value=link_val)

        valor_index = VALORES_IMOVEL.index(valor_val) if valor_val in VALORES_IMOVEL else 0
        valor_imovel = st.selectbox("Valor do Imóvel", VALORES_IMOVEL, index=valor_index)

        st.markdown("### 📍 Origem")
        origem_index = ORIGENS.index(origem_val) if origem_val in ORIGENS else 0
        origem = st.selectbox("Origem", ORIGENS, index=origem_index)

        status_index = STATUS_LISTA.index(status_val) if status_val in STATUS_LISTA else 0
        status = st.selectbox("Status", STATUS_LISTA, index=status_index)

        st.markdown("### 🎯 Preferências do Cliente")
        quartos_desejados = st.number_input("Quartos desejados", min_value=0, step=1, value=int(quartos_desejados_val))
        banheiros_desejados = st.number_input("Banheiros desejados", min_value=0, step=1, value=int(banheiros_desejados_val))
        vagas_desejadas = st.number_input("Vagas desejadas", min_value=0, step=1, value=int(vagas_desejadas_val))
        metragem_desejada = st.number_input("Metragem desejada (m²)", min_value=0.0, step=5.0, value=float(metragem_desejada_val))
        bairro_desejado = st.text_input("Bairro desejado", value=bairro_desejado_val)

        observacoes = st.text_area("Observações", value=observacoes_val)

        col_salvar, col_deletar = st.columns(2)
        with col_salvar:
            if st.button("💾 Salvar", type="primary", use_container_width=True):
                if nome and telefone:
                    if lead_edit:
                        for i, lead in enumerate(st.session_state.leads):
                            if lead["id"] == lead_edit["id"]:
                                st.session_state.leads[i] = {
                                    "id": lead_edit["id"],
                                    "nome": nome,
                                    "telefone": telefone,
                                    "data_cadastro": lead_edit.get("data_cadastro", datetime.now().strftime("%d/%m/%Y")),
                                    "perfil": perfil,
                                    "codigo_imovel": codigo_imovel,
                                    "link_imovel": link_imovel,
                                    "valor_imovel": valor_imovel,
                                    "origem": origem,
                                    "status": status,
                                    "ultimo_contato": lead_edit.get("ultimo_contato"),
                                    "observacoes": observacoes,
                                    "quartos_desejados": quartos_desejados,
                                    "banheiros_desejados": banheiros_desejados,
                                    "vagas_desejadas": vagas_desejadas,
                                    "metragem_desejada": metragem_desejada,
                                    "bairro_desejado": bairro_desejado,
                                    "mensagens_enviadas": lead_edit.get("mensagens_enviadas", [])
                                }
                                st.success(f"✅ {nome} atualizado!")
                                break
                    else:
                        novo_id = max([l["id"] for l in st.session_state.leads], default=0) + 1
                        novo_lead = {
                            "id": novo_id,
                            "nome": nome,
                            "telefone": telefone,
                            "data_cadastro": datetime.now().strftime("%d/%m/%Y"),
                            "perfil": perfil,
                            "codigo_imovel": codigo_imovel,
                            "link_imovel": link_imovel,
                            "valor_imovel": valor_imovel,
                            "origem": origem,
                            "status": status,
                            "ultimo_contato": None,
                            "observacoes": observacoes,
                            "quartos_desejados": quartos_desejados,
                            "banheiros_desejados": banheiros_desejados,
                            "vagas_desejadas": vagas_desejadas,
                            "metragem_desejada": metragem_desejada,
                            "bairro_desejado": bairro_desejado,
                            "mensagens_enviadas": []
                        }
                        st.session_state.leads.append(novo_lead)
                        st.success(f"✅ {nome} cadastrado!")

                    if salvar_leads(st.session_state.leads):
                        st.success("✅ Dados salvos no Google Sheets!")
                    st.rerun()
                else:
                    st.error("❌ Nome e telefone são obrigatórios!")

        with col_deletar:
            if lead_edit:
                if st.button("🗑️ Deletar", use_container_width=True):
                    st.session_state.leads = [l for l in st.session_state.leads if l["id"] != lead_edit["id"]]
                    if salvar_leads(st.session_state.leads):
                        st.success(f"✅ {lead_edit['nome']} removido!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Métricas")
        if metricas:
            st.metric("Total Leads", metricas["total_leads"])
            st.metric("Convertidos", metricas["convertidos"])
            st.metric("Taxa Conversão", f"{metricas['taxa_conversao']:.1f}%")

        st.markdown("---")
        st.markdown("### 💾 Backup")
        if st.button("📥 Exportar Backup (JSON)", use_container_width=True):
            backup_nome = f"backup_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_nome, "w", encoding="utf-8") as f:
                json.dump(st.session_state.leads, f, indent=2, ensure_ascii=False)
            st.success(f"✅ Backup salvo: {backup_nome}")

        uploaded_file = st.file_uploader("📤 Restaurar (JSON)", type=["json"], key="restore")
        if uploaded_file is not None:
            dados = json.load(uploaded_file)
            st.session_state.leads = dados
            if salvar_leads(st.session_state.leads):
                st.success("✅ Backup restaurado!")
            st.rerun()

        st.markdown("---")
        st.markdown("### ☁️ Google Sheets")
        if st.button("🔄 Forçar Sincronização", use_container_width=True):
            if salvar_leads(st.session_state.leads):
                st.success("✅ Dados sincronizados com o Google Sheets!")
            else:
                st.error("❌ Erro ao sincronizar. Verifique o Secret do Google.")

    # ==================== ABAS ====================
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📱 Leads e Mensagens", "📊 Análise e IA", "✏️ Gerenciar Mensagens", "📅 Agenda", "🏢 Imóveis"])

    # ==================== TAB 1 - LEADS E MENSAGENS ====================
    with tab1:
        st.subheader("📋 Lista de Leads")
        if st.session_state.leads:
            for i, lead in enumerate(st.session_state.leads):
                temp = calcular_temperatura(lead)
                temp_icon = "🔥" if temp == "quente" else "🌡️" if temp == "morno" else "❄️" if temp == "frio" else "🆕"
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.5, 1.2, 1.2, 1, 0.5])
                    with col1: st.markdown(f"{temp_icon} **{lead['nome']}**")
                    with col2: st.write(lead["telefone"])
                    with col3: st.write(lead.get("codigo_imovel", "-"))
                    with col4: st.write(lead.get("valor_imovel", "-"))
                    with col5: st.write(lead.get("origem", "-"))
                    with col6:
                        if st.button("📋", key=f"sel_{lead['id']}", help="Selecionar"):
                            st.session_state.lead_selecionado = lead["nome"]
                            st.rerun()
                    st.divider()

            st.caption(f"📊 Total: {len(st.session_state.leads)} leads")
            st.markdown("---")

            # Filtros
            st.markdown("### 🔍 Filtros")
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                filtro_perfil = st.selectbox("Perfil", ["Todos"] + list(PERFIS.keys()), format_func=lambda x: PERFIS[x]["titulo"] if x != "Todos" else "Todos")
            with col_f2:
                filtro_temp = st.selectbox("Temperatura", ["Todos", "quente", "morno", "frio", "novo"])
            with col_f3:
                filtro_origem = st.selectbox("Origem", ["Todos"] + ORIGENS)
            with col_f4:
                if st.button("❄️ Quem esfriou?", use_container_width=True):
                    filtro_temp = "frio"
                    st.rerun()

            leads_filtrados = st.session_state.leads.copy()
            if filtro_perfil != "Todos":
                leads_filtrados = [l for l in leads_filtrados if l["perfil"] == filtro_perfil]
            if filtro_temp != "Todos":
                leads_filtrados = [l for l in leads_filtrados if calcular_temperatura(l) == filtro_temp]
            if filtro_origem != "Todos":
                leads_filtrados = [l for l in leads_filtrados if l.get("origem") == filtro_origem]

            st.info(f"📌 Mostrando {len(leads_filtrados)} leads")

            if leads_filtrados:
                nomes = [l["nome"] for l in leads_filtrados]
                lead_selecionado = st.selectbox("Selecione um lead para mensagem:", nomes)
                lead_data = next(l for l in leads_filtrados if l["nome"] == lead_selecionado)
                st.markdown("---")

                # Cards
                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                with col_a:
                    temp = calcular_temperatura(lead_data)
                    if temp == "quente":
                        st.success(f"🔥 {temp.upper()} - Prioridade!")
                    elif temp == "morno":
                        st.warning(f"🌡️ {temp.upper()} - Acompanhar")
                    elif temp == "frio":
                        st.error(f"❄️ {temp.upper()} - Reativar")
                    else:
                        st.info(f"🆕 {temp.upper()} - Novo")
                with col_b:
                    st.metric("Perfil", PERFIS[lead_data["perfil"]]["titulo"])
                with col_c:
                    st.metric("Status", lead_data.get("status", "ativo"))
                with col_d:
                    st.metric("Origem", lead_data.get("origem", "-"))
                with col_e:
                    st.metric("Valor", lead_data.get("valor_imovel", "-"))

                # Imóvel
                st.markdown("---")
                st.subheader("🏠 Informações do Imóvel")
                col_im1, col_im2 = st.columns(2)
                with col_im1:
                    st.markdown(f"**Código:** {lead_data.get('codigo_imovel', '-')}")
                    st.markdown(f"**Valor:** {lead_data.get('valor_imovel', '-')}")
                with col_im2:
                    if lead_data.get("link_imovel"):
                        st.markdown(f"**Link:** [Abrir imóvel]({lead_data['link_imovel']})")
                    else:
                        st.markdown("**Link:** Não informado")

                if metricas and lead_data["perfil"] in metricas["conversao_por_perfil"]:
                    taxa = metricas["conversao_por_perfil"][lead_data["perfil"]]
                    st.info(f"🤖 **IA Recomenda:** Este perfil tem {taxa:.0f}% de conversão!")

                # ==================== RECOMENDAÇÕES DE IMÓVEIS ====================
                st.markdown("---")
                st.subheader("📌 Imóveis recomendados")
                imoveis_recomendados = recomendar_imoveis(lead_data, st.session_state.imoveis, tolerancia_valor=0.15, tolerancia_metragem=0.10)
                if imoveis_recomendados:
                    for imv in imoveis_recomendados[:5]:
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.markdown(f"**{imv['codigo']}** – {imv['valor']} – {imv['quartos']} quartos, {imv['banheiros']} banheiros, {imv['vagas']} vagas, {imv['metragem']}m² – {imv['bairro']}, {imv['rua']}")
                            with col2:
                                if imv['link']:
                                    st.link_button("🔗 Ver anúncio", imv['link'], use_container_width=True)
                            with col3:
                                msg_recomendacao = f"Olá {lead_data['nome'].split()[0]}! Encontrei um imóvel que pode te atender:\n\nCódigo: {imv['codigo']}\nValor: {imv['valor']}\nQuartos: {imv['quartos']}\nBanheiros: {imv['banheiros']}\nVagas: {imv['vagas']}\nMetragem: {imv['metragem']}m²\nBairro: {imv['bairro']}\nRua: {imv['rua']}\nLink: {imv['link']}\n\nO que achou? Posso agendar uma visita!"
                                telefone_limpo = re.sub(r"\D", "", lead_data["telefone"])
                                link_whats = f"https://api.whatsapp.com/send?phone=55{telefone_limpo}&text={urllib.parse.quote(msg_recomendacao)}"
                                st.link_button("💚 Recomendar", link_whats, use_container_width=True)
                            st.divider()
                else:
                    st.info("Nenhum imóvel recomendado no momento. Ajuste os filtros ou cadastre mais imóveis.")

                # ==================== MENSAGEM PRONTA ====================
                st.markdown("---")
                st.subheader(f"📱 Mensagem para {lead_data['nome']}")
                mensagens_ativas = [m for m in st.session_state.mensagens_personalizadas if m.get("ativa", True)]

                if mensagens_ativas:
                    col_msg_sel1, col_msg_sel2 = st.columns([3, 1])
                    with col_msg_sel1:
                        opcoes_mensagem = ["🤖 Mensagem Automática (IA)"] + [f"{m['titulo']} - {m['categoria']}" for m in mensagens_ativas]
                        msg_escolhida = st.selectbox("Escolha o tipo de mensagem:", opcoes_mensagem, key=f"sel_msg_{lead_data['id']}")
                    with col_msg_sel2:
                        st.markdown("###")
                        if st.button("🔄 Atualizar", use_container_width=True, key=f"atualizar_{lead_data['id']}"):
                            st.rerun()

                    if msg_escolhida != "🤖 Mensagem Automática (IA)":
                        idx = opcoes_mensagem.index(msg_escolhida) - 1
                        msg_template = mensagens_ativas[idx]["mensagem"]
                        nome_msg = lead_data["nome"].split()[0]
                        codigo = lead_data.get("codigo_imovel", "")
                        valor = lead_data.get("valor_imovel", "")
                        link = lead_data.get("link_imovel", "")
                        try:
                            mensagem = msg_template.format(nome=nome_msg, codigo=codigo, valor=valor, link=link)
                        except Exception:
                            mensagem = msg_template
                    else:
                        temperatura = calcular_temperatura(lead_data)
                        mensagem = gerar_mensagem_ia(lead_data, temperatura)
                else:
                    temperatura = calcular_temperatura(lead_data)
                    mensagem = gerar_mensagem_ia(lead_data, temperatura)
                    st.info("💡 Crie mensagens personalizadas na aba 'Gerenciar Mensagens'")

                st.markdown("### 💬 Mensagem Pronta:")
                st.info(mensagem)
                mensagem_editavel = st.text_area("✏️ Editar mensagem (se necessário):", mensagem, height=150, key=f"msg_{lead_data['id']}")

                st.markdown("### 🎯 Ações:")
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                with col_btn1:
                    if st.button("📋 Copiar Mensagem", use_container_width=True):
                        st.success("✅ Mensagem copiada!")
                with col_btn2:
                    if st.button("📞 Copiar Número", use_container_width=True):
                        st.success(f"✅ Número copiado: {lead_data['telefone']}")
                with col_btn3:
                    telefone_limpo = formatar_telefone(lead_data["telefone"])
                    mensagem_whats = str(mensagem_editavel).strip()
                    params = urllib.parse.urlencode(
                        {
                            "phone": f"55{telefone_limpo}",
                            "text": mensagem_whats,
                        },
                        quote_via=urllib.parse.quote,
                        encoding="utf-8",
                        errors="strict",
                    )
                    link_whats = f"https://api.whatsapp.com/send?{params}"
                    st.link_button("💚 Abrir WhatsApp", link_whats, use_container_width=True)
                    st.caption(f"📱 {lead_data['telefone']}")
                with col_btn4:
                    if st.button("✅ Marcar Enviado", use_container_width=True):
                        for lead in st.session_state.leads:
                            if lead["id"] == lead_data["id"]:
                                lead["ultimo_contato"] = datetime.now().strftime("%d/%m/%Y")
                                lead["mensagens_enviadas"].append({
                                    "data": datetime.now().strftime("%d/%m/%Y"),
                                    "mensagem": mensagem_editavel[:100]
                                })
                                if salvar_leads(st.session_state.leads):
                                    st.success("✅ Mensagem registrada! Último contato atualizado.")
                                st.rerun()
                                break

                with st.expander("📞 Ver informações completas"):
                    st.markdown(f"**Nome:** {lead_data['nome']}")
                    st.markdown(f"**Telefone:** {lead_data['telefone']}")
                    st.markdown(f"**Data Cadastro:** {lead_data.get('data_cadastro', '-')}")
                    st.markdown(f"**Perfil:** {PERFIS[lead_data['perfil']]['titulo']}")
                    st.markdown(f"**Origem:** {lead_data.get('origem', '-')}")
                    st.markdown(f"**Código Imóvel:** {lead_data.get('codigo_imovel', '-')}")
                    st.markdown(f"**Link Imóvel:** {lead_data.get('link_imovel', '-')}")
                    st.markdown(f"**Valor Imóvel:** {lead_data.get('valor_imovel', '-')}")
                    st.markdown(f"**Status:** {lead_data.get('status', '-')}")
                    st.markdown(f"**Último Contato:** {lead_data.get('ultimo_contato', 'Nunca')}")
                    st.markdown(f"**Observações:** {lead_data.get('observacoes', '-')}")
                    st.markdown(f"**Quartos desejados:** {lead_data.get('quartos_desejados', '-')}")
                    st.markdown(f"**Banheiros desejados:** {lead_data.get('banheiros_desejados', '-')}")
                    st.markdown(f"**Vagas desejadas:** {lead_data.get('vagas_desejadas', '-')}")
                    st.markdown(f"**Metragem desejada:** {lead_data.get('metragem_desejada', '-')} m²")
                    st.markdown(f"**Bairro desejado:** {lead_data.get('bairro_desejado', '-')}")
                    if lead_data.get("mensagens_enviadas"):
                        st.markdown("**📨 Últimas mensagens:**")
                        for msg in lead_data["mensagens_enviadas"][-3:]:
                            st.markdown(f"- {msg['data']}: {msg['mensagem'][:50]}...")

                st.markdown("---")
                st.subheader("📝 Atualizar Status")
                col_up1, col_up2 = st.columns(2)
                with col_up1:
                    novo_status = st.selectbox("Status", STATUS_LISTA, index=STATUS_LISTA.index(lead_data.get("status", "novo")))
                with col_up2:
                    if st.button("💾 Salvar Status", use_container_width=True):
                        for lead in st.session_state.leads:
                            if lead["id"] == lead_data["id"]:
                                lead["status"] = novo_status
                                if salvar_leads(st.session_state.leads):
                                    st.success("✅ Status atualizado!")
                                st.rerun()
                                break
            else:
                st.info("Nenhum lead encontrado com os filtros selecionados.")
        else:
            st.info("Nenhum lead cadastrado. Cadastre um na barra lateral.")

    # ==================== TAB 2 - ANÁLISE ====================
    with tab2:
        st.subheader("📊 Análise de Dados e Recomendações")
        if metricas and metricas["total_leads"] > 0:
            perfis = list(metricas["conversao_por_perfil"].keys())
            taxas = list(metricas["conversao_por_perfil"].values())
            df_graf = pd.DataFrame({"Perfil": [PERFIS[p]["titulo"] for p in perfis], "Conversão (%)": taxas})
            fig = px.bar(df_graf, x="Perfil", y="Conversão (%)", title="Qual perfil converte mais?", color="Conversão (%)", color_continuous_scale="Viridis", text="Conversão (%)")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📈 Métricas Gerais")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1: st.metric("Total de Leads", metricas["total_leads"])
            with col_m2: st.metric("Leads Convertidos", metricas["convertidos"])
            with col_m3: st.metric("Taxa de Conversão", f"{metricas['taxa_conversao']:.1f}%")
            with col_m4: st.metric("Em Andamento", metricas["total_leads"] - metricas["convertidos"])

            st.markdown("### 🌡️ Distribuição por Temperatura")
            temperaturas = [calcular_temperatura(l) for l in st.session_state.leads]
            temp_count = pd.Series(temperaturas).value_counts()
            for temp, count in temp_count.items():
                icon = "🔥" if temp == "quente" else "🌡️" if temp == "morno" else "❄️" if temp == "frio" else "🆕"
                st.markdown(f"- {icon} {temp.capitalize()}: {count}")

            st.markdown("---")
            st.markdown("### 💡 Dicas Práticas")
            melhor_perfil = max(metricas["conversao_por_perfil"].items(), key=lambda x: x[1])
            st.success(f"🎯 **Foco no perfil que mais converte:** {PERFIS[melhor_perfil[0]]['titulo']} com {melhor_perfil[1]:.0f}% de conversão!")
            st.info("""
            📌 **Checklist Semanal:**
            - [ ] Enviar mensagens toda sexta-feira (alerta automático!)
            - [ ] Priorizar leads QUENTES (contato nos últimos 3 dias)
            - [ ] Reativar leads FRIOS (mais de 10 dias sem contato)
            - [ ] Registrar todas as interações
            - [ ] Usar as mensagens personalizadas por perfil e imóvel
            """)

            st.markdown("### 📅 Calendário de Envios")
            hoje = datetime.now()
            dias_ate_sexta = (4 - hoje.weekday()) % 7
            if dias_ate_sexta == 0:
                st.success("🎉 **HOJE É SEXTA-FEIRA!** Hora de enviar mensagens! 🎉")
            else:
                st.info(f"📆 Próxima sexta-feira: **{dias_ate_sexta} dias**")
                st.markdown("✅ **Meta:** Enviar mensagens para todos os leads mornos e frios até sexta")
        else:
            st.info("Cadastre mais leads para gerar análises e recomendações!")

    # ==================== TAB 3 - GERENCIAR MENSAGENS ====================
    with tab3:
        st.subheader("✏️ Gerenciar Mensagens Personalizadas")
        st.markdown("Crie, edite e gerencie suas próprias mensagens para usar no WhatsApp.")
        sub_tab1, sub_tab2 = st.tabs(["📝 Criar Nova Mensagem", "📋 Minhas Mensagens"])

        with sub_tab1:
            st.markdown("### ✨ Criar Nova Mensagem")
            st.markdown("Use as variáveis: `{nome}`, `{codigo}`, `{valor}`, `{link}`")
            titulo = st.text_input("Título da Mensagem (ex: Sextou - Leads Quentes)")
            categoria = st.selectbox("Categoria", ["sexta", "acompanhamento", "reativacao", "oportunidade", "personalizada"])
            mensagem_nova = st.text_area(
                "Escreva sua mensagem (use {nome}, {codigo}, {valor}, {link})",
                height=200,
                placeholder="Exemplo:\nOlá {nome}! 🏠✨\n\nSobre o imóvel {codigo} no valor de {valor}, tenho uma novidade: {link}"
            )
            col_criar1, col_criar2 = st.columns(2)
            with col_criar1:
                if st.button("💾 Salvar Mensagem", type="primary", use_container_width=True):
                    if titulo and mensagem_nova:
                        novo_id = max([m["id"] for m in st.session_state.mensagens_personalizadas], default=0) + 1
                        nova_msg = {
                            "id": novo_id,
                            "titulo": titulo,
                            "categoria": categoria,
                            "mensagem": mensagem_nova,
                            "ativa": True
                        }
                        st.session_state.mensagens_personalizadas.append(nova_msg)
                        if salvar_mensagens(st.session_state.mensagens_personalizadas):
                            st.success(f"✅ Mensagem '{titulo}' salva com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Título e mensagem são obrigatórios!")
            with col_criar2:
                st.markdown("**💡 Dica:**")
                st.markdown("""
                - `{nome}` = Nome do cliente
                - `{codigo}` = Código do imóvel
                - `{valor}` = Valor do imóvel
                - `{link}` = Link do imóvel

                **Exemplo:** "Olá {nome}! O imóvel {codigo} no valor de {valor}... {link}"
                """)

        with sub_tab2:
            st.markdown("### 📋 Minhas Mensagens Personalizadas")
            if st.session_state.mensagens_personalizadas:
                categorias = ["Todas"] + list(set([m["categoria"] for m in st.session_state.mensagens_personalizadas]))
                filtro_cat = st.selectbox("Filtrar por categoria", categorias)
                mensagens_filtradas = st.session_state.mensagens_personalizadas
                if filtro_cat != "Todas":
                    mensagens_filtradas = [m for m in mensagens_filtradas if m["categoria"] == filtro_cat]

                for msg in mensagens_filtradas:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 1.5, 1, 0.5])
                        with col1:
                            status_msg = "✅ Ativa" if msg.get("ativa", True) else "⭕ Inativa"
                            st.markdown(f"**{msg['titulo']}**")
                            st.caption(f"Categoria: {msg['categoria']} | {status_msg}")
                        with col2:
                            with st.expander("📄 Ver mensagem"):
                                st.text(msg["mensagem"])
                        with col3:
                            if st.button(f"✏️ Editar", key=f"edit_{msg['id']}", use_container_width=True):
                                st.session_state.editando_msg = msg["id"]
                                st.rerun()
                        with col4:
                            if st.button("🗑️", key=f"del_msg_{msg['id']}", help="Deletar"):
                                st.session_state.mensagens_personalizadas = [m for m in st.session_state.mensagens_personalizadas if m["id"] != msg["id"]]
                                if salvar_mensagens(st.session_state.mensagens_personalizadas):
                                    st.success("✅ Mensagem removida!")
                                st.rerun()
                        st.divider()

                if "editando_msg" in st.session_state:
                    msg_edit = next(m for m in st.session_state.mensagens_personalizadas if m["id"] == st.session_state.editando_msg)
                    st.markdown("---")
                    st.markdown("### ✏️ Editando Mensagem")

                    categorias_msg = ["sexta", "acompanhamento", "reativacao", "oportunidade", "personalizada"]
                    categoria_atual = str(msg_edit.get("categoria", "personalizada") or "personalizada")
                    if categoria_atual not in categorias_msg:
                        categoria_atual = "personalizada"

                    novo_titulo = st.text_input("Título", value=str(msg_edit.get("titulo", "") or ""), key=f"edit_titulo_{msg_edit['id']}")
                    nova_categoria = st.selectbox("Categoria", categorias_msg, index=categorias_msg.index(categoria_atual), key=f"edit_categoria_{msg_edit['id']}")
                    nova_mensagem = st.text_area("Mensagem", value=str(msg_edit.get("mensagem", "") or ""), height=150, key=f"edit_mensagem_{msg_edit['id']}")
                    ativa = st.checkbox("Ativa", value=bool(msg_edit.get("ativa", True)), key=f"edit_ativa_{msg_edit['id']}")

                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button("💾 Salvar Alterações", type="primary", key=f"salvar_msg_{msg_edit['id']}"):
                            for m in st.session_state.mensagens_personalizadas:
                                if m["id"] == msg_edit["id"]:
                                    m["titulo"] = novo_titulo
                                    m["categoria"] = nova_categoria
                                    m["mensagem"] = nova_mensagem
                                    m["ativa"] = ativa
                                    break
                            if salvar_mensagens(st.session_state.mensagens_personalizadas):
                                st.success("✅ Mensagem atualizada!")
                            del st.session_state.editando_msg
                            st.rerun()
                    with col_edit2:
                        if st.button("❌ Cancelar", key=f"cancelar_msg_{msg_edit['id']}"):
                            del st.session_state.editando_msg
                            st.rerun()
            else:
                st.info("Nenhuma mensagem personalizada. Crie sua primeira mensagem!")

    # ==================== TAB 4 - AGENDA ====================
    with tab4:
        compromissos_hoje_count = len(get_compromissos_hoje(st.session_state.compromissos))
        if compromissos_hoje_count > 0:
            st.subheader(f"📅 Agenda de Compromissos 🔔 {compromissos_hoje_count} hoje!")
        else:
            st.subheader("📅 Agenda de Compromissos")
        st.markdown("Gerencie visitas, ligações e reuniões")

        data_selecionada = st.date_input("📆 Selecione a data:", datetime.now())
        data_str = data_selecionada.strftime("%d/%m/%Y")
        st.markdown("---")
        st.markdown(f"### 📌 Compromissos do dia {data_str}")
        compromissos_hoje = get_compromissos_do_dia(st.session_state.compromissos, data_str)

        if compromissos_hoje:
            for comp in compromissos_hoje:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 0.5])
                    with col1:
                        tipo = comp.get("tipo", "visita")
                        if tipo == "visita":
                            st.markdown(f"🏠 **{comp['titulo']}**")
                        elif tipo == "ligacao":
                            st.markdown(f"📞 **{comp['titulo']}**")
                        else:
                            st.markdown(f"📌 **{comp['titulo']}**")
                        st.caption(comp.get("horario", ""))
                    with col2:
                        st.write(f"👤 {comp.get('lead_nome', '')}")
                    with col3:
                        if st.button(f"✅ Concluir", key=f"concluir_{comp['id']}", use_container_width=True):
                            st.session_state.compromissos = [c for c in st.session_state.compromissos if c["id"] != comp["id"]]
                            if salvar_compromissos(st.session_state.compromissos):
                                st.success("✅ Concluído!")
                            st.rerun()
                    with col4:
                        if st.button(f"🗑️", key=f"del_comp_{comp['id']}"):
                            st.session_state.compromissos = [c for c in st.session_state.compromissos if c["id"] != comp["id"]]
                            if salvar_compromissos(st.session_state.compromissos):
                                st.success("✅ Removido!")
                            st.rerun()
                    st.divider()
        else:
            st.info(f"📭 Nenhum compromisso para {data_str}")

        st.markdown("---")
        st.markdown("### ✨ Novo Compromisso")
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            if st.session_state.leads:
                leads_opcoes = ["-- Selecione um lead --"] + [l["nome"] for l in st.session_state.leads]
                lead_selecionado = st.selectbox("Lead relacionado", leads_opcoes, key="lead_agenda")
            else:
                lead_selecionado = "-- Selecione um lead --"
            titulo = st.text_input("Título do compromisso*", key="titulo_agenda")
            tipo = st.selectbox("Tipo", ["visita", "ligacao", "reuniao", "outro"], key="tipo_agenda")
        with col_form2:
            data_comp = st.date_input("Data", datetime.now(), key="data_agenda")
            horario = st.time_input("Horário", key="horario_agenda")
            observacoes_comp = st.text_area("Observações", key="obs_agenda")
        if st.button("📅 Agendar", type="primary", use_container_width=True):
            if titulo:
                novo_id = max([c["id"] for c in st.session_state.compromissos], default=0) + 1
                lead_nome = lead_selecionado if lead_selecionado != "-- Selecione um lead --" else ""
                novo_comp = {
                    "id": novo_id,
                    "titulo": titulo,
                    "tipo": tipo,
                    "data": data_comp.strftime("%d/%m/%Y"),
                    "horario": horario.strftime("%H:%M"),
                    "lead_nome": lead_nome,
                    "observacoes": observacoes_comp,
                    "criado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.session_state.compromissos.append(novo_comp)
                if salvar_compromissos(st.session_state.compromissos):
                    st.success(f"✅ Agendado para {data_comp.strftime('%d/%m/%Y')} às {horario.strftime('%H:%M')}!")
                st.rerun()
            else:
                st.error("❌ Título obrigatório!")

        st.markdown("---")
        st.markdown("### 📋 Próximos Compromissos")
        hoje = datetime.now().strftime("%d/%m/%Y")
        futuros = [c for c in st.session_state.compromissos if c.get("data") >= hoje]
        futuros.sort(key=lambda x: (x.get("data", ""), x.get("horario", "")))
        if futuros:
            for comp in futuros[:5]:
                icon = "🏠" if comp["tipo"] == "visita" else "📞" if comp["tipo"] == "ligacao" else "🤝" if comp["tipo"] == "reuniao" else "📌"
                st.markdown(f"- {icon} **{comp['titulo']}** - {comp['data']} às {comp['horario']} - {comp.get('lead_nome', 'Sem lead')}")
        else:
            st.info("Nenhum compromisso futuro")

    # ==================== TAB 5 - IMÓVEIS ====================
    with tab5:
        st.subheader("🏢 Base de Imóveis")
        st.markdown("Cadastre e edite os imóveis do seu acervo.")

        # Formulário para novo imóvel
        with st.expander("➕ Novo Imóvel", expanded=False):
            codigo = st.text_input("Código*")
            valor = st.selectbox("Valor", VALORES_IMOVEL)
            quartos = st.number_input("Quartos", min_value=0, step=1)
            banheiros = st.number_input("Banheiros", min_value=0, step=1)
            vagas = st.number_input("Vagas", min_value=0, step=1)
            metragem = st.number_input("Metragem (m²)", min_value=0.0, step=5.0)
            bairro = st.text_input("Bairro")
            rua = st.text_input("Rua")
            link = st.text_input("Link do anúncio")
            opcionista = st.text_input("Opcionista (responsável pela informação)")

            if st.button("💾 Salvar Imóvel", type="primary"):
                if codigo and valor:
                    codigo_existente = any(i["codigo"] == codigo for i in st.session_state.imoveis)
                    link_existente = any(i["link"] == link for i in st.session_state.imoveis) if link else False
                    if codigo_existente:
                        st.error("❌ Já existe um imóvel com este código! Use um código diferente.")
                    elif link_existente:
                        st.error("❌ Já existe um imóvel com este link! Use um link diferente.")
                    else:
                        novo_id = max([i["id"] for i in st.session_state.imoveis], default=0) + 1
                        novo_imv = {
                            "id": novo_id,
                            "codigo": codigo,
                            "valor": valor,
                            "quartos": quartos,
                            "banheiros": banheiros,
                            "vagas": vagas,
                            "metragem": metragem,
                            "bairro": bairro,
                            "rua": rua,
                            "link": link,
                            "opcionista": opcionista
                        }
                        st.session_state.imoveis.append(novo_imv)
                        if salvar_imoveis(st.session_state.imoveis):
                            st.success("Imóvel cadastrado com sucesso!")
                        st.rerun()
                else:
                    st.error("Código e valor são obrigatórios.")

        # Lista de imóveis existentes
        st.markdown("### 📋 Imóveis Cadastrados")
        if st.session_state.imoveis:
            df_imoveis = pd.DataFrame(st.session_state.imoveis)
            st.dataframe(df_imoveis, use_container_width=True, hide_index=True)

            # Seção de edição
            st.markdown("---")
            st.markdown("### ✏️ Editar Imóvel")
            ids_imoveis = [i["id"] for i in st.session_state.imoveis]
            id_editar = st.selectbox("Selecione o ID do imóvel para editar", ids_imoveis, key="editar_imovel_id")
            imv_editar = next(i for i in st.session_state.imoveis if i["id"] == id_editar)

            with st.form(key="form_editar_imovel"):
                novo_codigo = st.text_input("Código", value=imv_editar["codigo"])
                novo_valor = st.selectbox("Valor", VALORES_IMOVEL, index=VALORES_IMOVEL.index(imv_editar["valor"]) if imv_editar["valor"] in VALORES_IMOVEL else 0)
                novo_quartos = st.number_input("Quartos", value=int(imv_editar["quartos"]) if imv_editar["quartos"] else 0, step=1)
                novo_banheiros = st.number_input("Banheiros", value=int(imv_editar["banheiros"]) if imv_editar["banheiros"] else 0, step=1)
                novo_vagas = st.number_input("Vagas", value=int(imv_editar["vagas"]) if imv_editar["vagas"] else 0, step=1)
                novo_metragem = st.number_input("Metragem (m²)", value=float(imv_editar["metragem"]) if imv_editar["metragem"] else 0.0, step=5.0)
                novo_bairro = st.text_input("Bairro", value=imv_editar["bairro"])
                novo_rua = st.text_input("Rua", value=imv_editar["rua"])
                novo_link = st.text_input("Link do anúncio", value=imv_editar["link"])
                novo_opcionista = st.text_input("Opcionista", value=imv_editar["opcionista"])

                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    submitted = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
                with col_edit2:
                    cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)

                if submitted:
                    codigo_existente = any(i["codigo"] == novo_codigo and i["id"] != id_editar for i in st.session_state.imoveis)
                    link_existente = any(i["link"] == novo_link and i["id"] != id_editar for i in st.session_state.imoveis) if novo_link else False
                    if codigo_existente:
                        st.error("❌ Já existe outro imóvel com este código! Use um código diferente.")
                    elif link_existente:
                        st.error("❌ Já existe outro imóvel com este link! Use um link diferente.")
                    else:
                        for i in st.session_state.imoveis:
                            if i["id"] == id_editar:
                                i["codigo"] = novo_codigo
                                i["valor"] = novo_valor
                                i["quartos"] = novo_quartos
                                i["banheiros"] = novo_banheiros
                                i["vagas"] = novo_vagas
                                i["metragem"] = novo_metragem
                                i["bairro"] = novo_bairro
                                i["rua"] = novo_rua
                                i["link"] = novo_link
                                i["opcionista"] = novo_opcionista
                                break
                        if salvar_imoveis(st.session_state.imoveis):
                            st.success("Imóvel atualizado com sucesso!")
                        st.rerun()

                if cancel:
                    st.rerun()

            # Opção de deletar
            st.markdown("---")
            col_del1, col_del2 = st.columns([1, 3])
            with col_del1:
                id_deletar = st.number_input("ID do imóvel para deletar", min_value=0, step=1, key="del_imovel_id")
            with col_del2:
                if st.button("🗑️ Deletar Imóvel", use_container_width=True):
                    st.session_state.imoveis = [i for i in st.session_state.imoveis if i["id"] != id_deletar]
                    if salvar_imoveis(st.session_state.imoveis):
                        st.success(f"Imóvel ID {id_deletar} removido!")
                    st.rerun()
        else:
            st.info("Nenhum imóvel cadastrado. Cadastre o primeiro acima.")

if __name__ == "__main__":
    main()
