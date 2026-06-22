import streamlit as st
import json
import hashlib
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import re
import io
from scipy.stats import norm
import time
import requests
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import yfinance as yf
import csv
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# ========== CONFIGURAÇÃO DA PÁGINA (ÚNICA VEZ) ==========
st.set_page_config(
    page_title="Gamma Points Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# =============================================================================
# FUNÇÃO calcular_cvs DEFINIDA PRIMEIRO (USADA POR TODAS)
# =============================================================================
def calcular_cvs(strike, basis, spot):
    """
    Calcula o CVS (Centavos por Vol) para um strike específico
    
    Fórmula: CVS = strike × (basis / spot)
    
    Regra:
    - Se basis == 1: retorna 0 (mostra 00000)
    - Se basis != 1: aplica a fórmula normalmente
    
    Args:
        strike (float): Preço do strike
        basis (float): Basis de conversão
        spot (float): Preço spot atual
    
    Returns:
        int: Valor do CVS arredondado para 5 dígitos
    """
    if basis is None or spot is None or basis == 0 or spot == 0:
        return 0
    
    # Se basis = 1, sistema desligado
    if basis == 1:
        return 0
    
    # Aplica a fórmula: strike × (basis / spot)
    cvs = strike * (basis / spot)
    
    # Arredondar para inteiro
    return int(round(cvs))


# ========== FUNÇÃO PLOTLY OTIMIZADA PARA CHROME ==========
def plotly_chart_optimized(fig, key, use_container_width=True, height=None):
    """
    Versão otimizada do st.plotly_chart para Chrome
    Também suporta figuras matplotlib (st.pyplot)
    """
    # Verificar se é uma figura matplotlib
    if hasattr(fig, 'get_tk_widget') or hasattr(fig, 'figure'):
        # É uma figura matplotlib (FigureCanvasTkAgg ou Figure)
        if hasattr(fig, 'figure'):
            # É FigureCanvasTkAgg
            fig_to_plot = fig.figure
        else:
            # É Figure diretamente
            fig_to_plot = fig
        
        # Usar st.pyplot para matplotlib
        return st.pyplot(fig_to_plot, use_container_width=use_container_width)
    
    # Caso contrário, é plotly
    config = {
        'displayModeBar': False,
        'responsive': True,
        'scrollZoom': True,
        'staticPlot': False,
        'autosizable': True,
        'doubleClick': 'reset',
        'showTips': False,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'gamma_chart',
            'scale': 1
        }
    }
    
    if height:
        config['height'] = height
    
    return st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        config=config,
        key=key
    )


def plotly_chart_optimized(fig, key, use_container_width=True, height=None):
    """
    Versão otimizada para exibir gráficos no Streamlit
    Suporta tanto Plotly quanto Matplotlib
    """
    # Verificar se é uma figura matplotlib
    if hasattr(fig, 'figure') or hasattr(fig, 'get_tk_widget') or isinstance(fig, plt.Figure):
        # É matplotlib - usar st.pyplot
        import matplotlib.pyplot as plt
        if hasattr(fig, 'figure'):
            # É FigureCanvasTkAgg
            fig_to_plot = fig.figure
        else:
            # É Figure diretamente
            fig_to_plot = fig
        
        # Ajustar tamanho se necessário
        if height:
            fig_to_plot.set_figheight(height / 100)  # converter pixels para polegadas
            fig_to_plot.set_figwidth(12)
        
        # Usar st.pyplot para matplotlib
        return st.pyplot(fig_to_plot, use_container_width=use_container_width)
    
    # Caso contrário, é plotly
    config = {
        'displayModeBar': False,
        'responsive': True,
        'scrollZoom': True,
        'staticPlot': False,
        'autosizable': True,
        'doubleClick': 'reset',
        'showTips': False,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'gamma_chart',
            'scale': 1
        }
    }
    
    if height:
        config['height'] = height
    
    return st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        config=config,
        key=key
    )

def render_chart(fig, key, use_container_width=True, height=None):
    """
    Função universal para renderizar gráficos no Streamlit
    Detecta automaticamente se é Plotly ou Matplotlib e usa o método correto
    """
    # Verificar se é uma figura matplotlib
    is_matplotlib = False
    
    if hasattr(fig, 'figure'):
        is_matplotlib = True
        fig_to_plot = fig.figure
    elif hasattr(fig, 'get_tk_widget'):
        is_matplotlib = True
        fig_to_plot = fig
    elif hasattr(fig, 'add_subplot'):
        is_matplotlib = True
        fig_to_plot = fig
    elif hasattr(fig, 'gca'):
        is_matplotlib = True
        fig_to_plot = fig
    elif hasattr(fig, 'data') and hasattr(fig, 'layout'):
        is_matplotlib = False
        fig_to_plot = fig
    else:
        import matplotlib.figure as mpl_figure
        if isinstance(fig, mpl_figure.Figure):
            is_matplotlib = True
            fig_to_plot = fig
        else:
            is_matplotlib = False
            fig_to_plot = fig
    
    if is_matplotlib:
        if height:
            fig_to_plot.set_figheight(height / 100)
            fig_to_plot.set_figwidth(12)
        return st.pyplot(fig_to_plot, use_container_width=use_container_width)
    else:
        config = {
            'displayModeBar': False,
            'responsive': True,
            'scrollZoom': True,
            'staticPlot': False,
            'autosizable': True,
            'doubleClick': 'reset',
            'showTips': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'gamma_chart',
                'scale': 1
            }
        }
        if height:
            config['height'] = height
        return st.plotly_chart(
            fig_to_plot,
            use_container_width=use_container_width,
            config=config,
            key=key
        )

# =============================================================================
# SISTEMA DE CACHE OTIMIZADO
# =============================================================================

@st.cache_data(ttl=86400, max_entries=20, show_spinner=False)
def cache_leitura_csv(file_content):
    """Cache para leitura do arquivo CSV"""
    return read_cboe_csv(file_content)


@st.cache_data(ttl=86400, max_entries=20, show_spinner=False)
def cache_calculo_exposicoes(df_original, spot, tuple_strikes):
    """Cache para cálculo de exposições (DEX, GEX, VANNA)"""
    strikes_list = list(tuple_strikes)
    return calcular_exposicoes(df_original, spot, strikes_list)


@st.cache_data(ttl=86400, max_entries=20, show_spinner=False)
def cache_gamma_profile_curvas(price_levels, total_gamma, gamma_ex_next, gamma_ex_fri, 
                               spot, basis, gamma_flip=None, vol_trigger=None):
    """
    Versão cacheada da criação do gráfico Gamma Profile
    """
    # Validar entradas
    if price_levels is None or len(price_levels) == 0:
        st.warning("⚠️ Nenhum dado de preço disponível para o gráfico.")
        return go.Figure()
    
    # Garantir que os arrays estão em formato numpy
    price_levels = np.array(price_levels)
    total_gamma = np.array(total_gamma) if total_gamma is not None else np.zeros_like(price_levels)
    gamma_ex_next = np.array(gamma_ex_next) if gamma_ex_next is not None else np.zeros_like(price_levels)
    gamma_ex_fri = np.array(gamma_ex_fri) if gamma_ex_fri is not None else np.zeros_like(price_levels)
    
    return criar_grafico_gamma_profile_curvas(
        price_levels=price_levels,
        total_gamma=total_gamma,
        gamma_ex_next=gamma_ex_next,
        gamma_ex_fri=gamma_ex_fri,
        spot=spot,
        basis=basis,
        gamma_flip=gamma_flip,
        vol_trigger=vol_trigger
    )


# ========== CSS OTIMIZADO PARA CHROME ==========
st.markdown("""
    <style>
        .stPlotlyChart {
            transform: translateZ(0);
            will-change: transform;
            -webkit-transform: translateZ(0);
            -webkit-will-change: transform;
        }
        
        * {
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
            -webkit-animation-duration: 0.01ms !important;
            -webkit-transition-duration: 0.01ms !important;
        }
        
        .stApp {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #2e2e2e;
        }
        ::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #777;
        }
        
        .stMarkdown {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        .stDataFrame {
            font-size: 12px;
        }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNÇÃO DE PROGRESSO PARA CÁLCULOS PESADOS
# =============================================================================

def calcular_com_progresso(func, *args, **kwargs):
    """Executa função pesada com indicador de progresso"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("⏳ Iniciando processamento...")
    progress_bar.progress(10)
    
    try:
        resultado = func(*args, **kwargs)
        progress_bar.progress(100)
        status_text.text("✅ Processamento concluído!")
        return resultado
    except Exception as e:
        status_text.text(f"❌ Erro: {str(e)}")
        raise
    finally:
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()


# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================
ARQUIVO_USUARIOS = "usuarios.json"


# =============================================================================
# AUTENTICAÇÃO
# =============================================================================
def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f).get("usuarios", [])
    return []


def hash_cpf(cpf):
    cpf_limpo = cpf.replace(".", "").replace("-", "").strip()
    return hashlib.sha256(cpf_limpo.encode('utf-8')).hexdigest()


def verificar_acesso():
    if st.session_state.get("autenticado"):
        return True
    
    st.title("🔒 Acesso Restrito ao Sistema")
    st.write("Por favor, insira suas credenciais para acessar o Gamma Points Dashboard.")
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("📧 Seu E-mail", placeholder="exemplo@dominio.com").strip().lower()
    with col2:
        cpf = st.text_input("🆔 Seu CPF", placeholder="000.000.000-00", type="password").strip()
    
    if st.button("🔓 Acessar Sistema", type="primary", use_container_width=True):
        usuarios = carregar_usuarios()
        cpf_hash_digitado = hash_cpf(cpf)
        
        usuario_encontrado = next((u for u in usuarios if u["email"] == email), None)
        
        if not usuario_encontrado:
            st.error("❌ E-mail não cadastrado no sistema.")
            return False
        if not usuario_encontrado.get("ativo", True):
            st.error("🚫 Acesso negado: Este usuário foi **bloqueado** pelo administrador.")
            return False
        if usuario_encontrado["cpf_hash"] != cpf_hash_digitado:
            st.error("❌ CPF incorreto para este e-mail.")
            return False
            
        st.session_state["autenticado"] = True
        st.session_state["email_usuario"] = email
        st.rerun()
    return False


# =============================================================================
# FUNÇÕES DE PROCESSAMENTO
# =============================================================================
def read_cboe_csv(file_content):
    try:
        content_str = file_content.decode('utf-8') if isinstance(file_content, bytes) else file_content
        lines = content_str.split('\n')
        
        symbol = "DESCONHECIDO"
        spot = 0.0
        data_str = None
        
        for line in lines[:6]:
            if 'Last:' in line:
                match = re.search(r'Last:\s*([0-9\.,]+)', line)
                if match:
                    spot = float(match.group(1).replace(',', ''))
                if ',' in line:
                    symbol = line.split(',')[0].strip()
            if 'Date:' in line:
                match = re.search(r'Date:\s*([^,]+)', line)
                if match:
                    data_str = match.group(1).strip()
        
        colunas = [
            'ExpirationDate', 'CallSymbol', 'CallLastSale', 'CallNet', 'CallBid', 'CallAsk',
            'CallVol', 'CallIV', 'CallDelta', 'CallGamma', 'CallOpenInt', 'Strike',
            'PutSymbol', 'PutLastSale', 'PutNet', 'PutBid', 'PutAsk', 'PutVol',
            'PutIV', 'PutDelta', 'PutGamma', 'PutOpenInt'
        ]
        
        data_lines = [line for line in lines[4:] if line.strip() and not line.startswith('Expiration')]
        df = pd.read_csv(io.StringIO('\n'.join(data_lines)), header=None, names=colunas, on_bad_lines='skip')
        
        df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], errors='coerce')
        
        calls = df[['ExpirationDate','Strike','CallDelta','CallGamma','CallOpenInt','CallVol','CallIV']].copy()
        calls.columns = ['ExpirationDate','Strike','Delta','Gamma','Open Interest','Volume','IV']
        calls['Type'] = 'Call'
        
        puts = df[['ExpirationDate','Strike','PutDelta','PutGamma','PutOpenInt','PutVol','PutIV']].copy()
        puts.columns = ['ExpirationDate','Strike','Delta','Gamma','Open Interest','Volume','IV']
        puts['Type'] = 'Put'
        
        result_df = pd.concat([calls, puts], ignore_index=True)
        
        for col in ['Strike', 'Delta', 'Gamma', 'Open Interest', 'Volume', 'IV']:
            result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
        
        result_df = result_df.dropna(subset=['ExpirationDate', 'Strike'])
        
        return symbol, spot, data_str, result_df
    except Exception as e:
        st.error(f"Erro ao ler CSV: {e}")
        return None, 0, None, None


def calcular_exposicoes(df, spot, strikes_selecionados):
    if not strikes_selecionados:
        return [], {}
    
    df = df[df['Strike'].isin(strikes_selecionados)].copy()
    if df.empty:
        return [], {}
    
    strikes = sorted(df['Strike'].unique())
    CONTRACT_MULTIPLIER = 100.0
    data_ref = datetime.now()
    
    df["DEX"] = df["Delta"] * df["Open Interest"] * CONTRACT_MULTIPLIER * spot
    df["GEX"] = df["Gamma"] * df["Open Interest"] * CONTRACT_MULTIPLIER * (spot ** 2) * 0.01
    
    df["T"] = (df["ExpirationDate"] - data_ref).dt.days / 365.0
    df["T"] = df["T"].clip(lower=1/365)
    df["sigma"] = (df["IV"] / 100.0).replace(0, np.nan)
    
    valid = df["sigma"].notna() & (df["sigma"] > 0)
    df.loc[valid, "d1"] = (np.log(spot / df.loc[valid, "Strike"]) + 0.5 * df.loc[valid, "sigma"]**2 * df.loc[valid, "T"]) / (df.loc[valid, "sigma"] * np.sqrt(df.loc[valid, "T"]))
    df.loc[valid, "d2"] = df.loc[valid, "d1"] - df.loc[valid, "sigma"] * np.sqrt(df.loc[valid, "T"])
    df.loc[valid, "VANNA_unit"] = - (df.loc[valid, "d2"] / df.loc[valid, "sigma"]) * df.loc[valid, "Gamma"]
    df["VANNA"] = df.loc[valid, "VANNA_unit"] * df.loc[valid, "Open Interest"] * CONTRACT_MULTIPLIER
    df["VANNA"] = df["VANNA"].replace([np.inf, -np.inf], 0).fillna(0)
    
    agg = df.groupby(["Strike", "Type"], as_index=False)[["Volume", "Open Interest", "DEX", "GEX", "VANNA"]].sum()
    
    pivots = {}
    for metric in ["Volume", "Open Interest", "DEX", "GEX", "VANNA"]:
        p = agg.pivot(index="Strike", columns="Type", values=metric).fillna(0)
        for col in ["Call", "Put"]:
            if col not in p.columns:
                p[col] = 0.0
        pivots[metric] = p
    
    return strikes, pivots


# =============================================================================
# GRÁFICOS
# =============================================================================
def criar_grafico_total_gamma_barras(df, spot, basis):
    """
    Cria o gráfico Total Gamma Exposure em BARRAS
    - Fundo preto (igual à aba Todos os Gráficos)
    - Call Wall e Put Wall com bolinhas
    - Barras azuis
    - Otimizado para performance
    """
    # ========== VERIFICAR COLUNAS DISPONÍVEIS ==========
    colunas_disponiveis = df.columns.tolist()

    # Verificar se estamos no formato CBOE (calls e puts separados)
    if 'CallGamma' in colunas_disponiveis and 'CallOpenInt' in colunas_disponiveis:
        # Formato CBOE - calcular GEX diretamente
        df_calc = df.copy()
        
        # Calcular GEX para Calls e Puts
        df_calc['CallGEX'] = df_calc['CallGamma'] * df_calc['CallOpenInt'] * 100 * spot * spot * 0.01
        df_calc['PutGEX'] = df_calc['PutGamma'] * df_calc['PutOpenInt'] * 100 * spot * spot * 0.01 * -1
        
        # Agregar por Strike
        dfAgg = df_calc.groupby(['Strike']).agg({
            'CallGEX': 'sum',
            'PutGEX': 'sum'
        }).reset_index()
        
        dfAgg['TotalGamma'] = (dfAgg['CallGEX'] + dfAgg['PutGEX']) / 10**9
        
        strikes = dfAgg['Strike'].values
        total_gamma = dfAgg['TotalGamma'].values
        total_gamma_sum = dfAgg['TotalGamma'].sum()
        
    # Verificar formato com colunas 'Type' (calls e puts em linhas separadas)
    elif 'Type' in colunas_disponiveis and 'Gamma' in colunas_disponiveis and 'Open Interest' in colunas_disponiveis:
        df_calc = df.copy()
        
        # Separar calls e puts
        calls = df_calc[df_calc['Type'] == 'Call'].copy()
        puts = df_calc[df_calc['Type'] == 'Put'].copy()
        
        # Calcular GEX para cada strike
        call_gex = calls.groupby('Strike').apply(
            lambda x: (x['Gamma'] * x['Open Interest'] * 100 * spot * spot * 0.01).sum(),
            include_groups=False
        )
        put_gex = puts.groupby('Strike').apply(
            lambda x: -(x['Gamma'] * x['Open Interest'] * 100 * spot * spot * 0.01).sum(),
            include_groups=False
        )
        
        # Combinar todos os strikes
        all_strikes = sorted(set(call_gex.index.tolist() + put_gex.index.tolist()))
        
        strikes = []
        total_gamma = []
        for s in all_strikes:
            call_val = call_gex.get(s, 0)
            put_val = put_gex.get(s, 0)
            gex_total = (call_val + put_val) / 10**9
            if abs(gex_total) > 0.001:
                strikes.append(s)
                total_gamma.append(gex_total)
        
        strikes = np.array(strikes)
        total_gamma = np.array(total_gamma)
        total_gamma_sum = sum(total_gamma) if len(total_gamma) > 0 else 0
        
    else:
        st.error("❌ Não foi possível calcular GEX. Colunas necessárias não encontradas.")
        st.info(f"Colunas disponíveis: {', '.join(colunas_disponiveis[:10])}...")
        return go.Figure()

    # Verificar se temos dados
    if len(strikes) == 0:
        st.warning("⚠️ Nenhum dado de GEX calculado.")
        return go.Figure()

    # ========== LIMITES DO EIXO X ==========
    fromStrike = 0.8 * spot
    toStrike = 1.2 * spot

    # ========== CRIAR GRÁFICO ==========
    fig = go.Figure()
    
    # ========== CVS PARA CADA STRIKE ==========
    cvs_values = [calcular_cvs(s, basis, spot) for s in strikes]

    # ========== HOVER TEMPLATE ==========
    hover_template = (
        "<b>STRIKE: %{x}</b><br>"
        "<b>CVS: %{customdata}</b>"
        "<extra></extra>"
    )

    # Barras verticais - AZUIS
    fig.add_trace(go.Bar(
        x=strikes,
        y=total_gamma,
        width=6,
        name='Gamma Exposure',
        marker_color='rgb(26, 118, 255)',
        marker_line_color='black',
        marker_line_width=0.15,
        customdata=cvs_values,
        hovertemplate=hover_template
    ))

    # Linha do zero - CINZA
    fig.add_hline(y=0, line_dash="solid", line_color="#888888", opacity=0.5)

    # Linha do Spot (branca tracejada)
    spot_cvs = calcular_cvs(spot, basis, spot)
    fig.add_vline(x=spot, line_dash="dash", line_color="white", line_width=2,
                  annotation_text=f'SPOT {spot:.0f} ({spot_cvs:04d})',
                  annotation_position="top",
                  annotation_font=dict(color='white'))

    # ========== CALL WALL E PUT WALL COM BOLINHAS ==========
    if len(total_gamma) > 0:
        # Call Wall - maior GEX positivo
        idx_max = np.argmax(total_gamma)
        strike_call = strikes[idx_max]
        call_wall_cvs = calcular_cvs(strike_call, basis, spot)
        
        fig.add_trace(go.Scatter(
            x=[strike_call], 
            y=[total_gamma[idx_max]],
            mode='markers', 
            marker=dict(
                color='blue', 
                size=12, 
                symbol='circle',
                line=dict(color='white', width=2)
            ),
            name=f'Call Wall {strike_call:.0f} ({call_wall_cvs:04d})',
            hoverinfo='text',
            text=f'Call Wall: {strike_call:.0f} ({call_wall_cvs:04d})<br>GEX: {total_gamma[idx_max]:.2f}B'
        ))
        
        # Put Wall - menor GEX negativo
        idx_min = np.argmin(total_gamma)
        strike_put = strikes[idx_min]
        put_wall_cvs = calcular_cvs(strike_put, basis, spot)
        
        fig.add_trace(go.Scatter(
            x=[strike_put], 
            y=[total_gamma[idx_min]],
            mode='markers', 
            marker=dict(
                color='red', 
                size=12, 
                symbol='circle',
                line=dict(color='white', width=2)
            ),
            name=f'Put Wall {strike_put:.0f} ({put_wall_cvs:04d})',
            hoverinfo='text',
            text=f'Put Wall: {strike_put:.0f} ({put_wall_cvs:04d})<br>GEX: {total_gamma[idx_min]:.2f}B'
        ))

    # ========== LAYOUT (FUNDO PRETO) ==========
    if len(strikes) > 15:
        step_ticks = max(1, len(strikes) // 15)
        x_ticks = strikes[::step_ticks]
    else:
        x_ticks = strikes
    
    x_labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in x_ticks]
    
    fig.update_layout(
        title={
            'text': f"Total Gamma: {total_gamma_sum:,.2f} Bn per 1% Move",
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#888888'}
        },
        xaxis_title='Strike',
        xaxis_title_font=dict(color='#888888'),
        yaxis_title='Spot Gamma Exposure ($ billions/1% move)',
        yaxis_title_font=dict(color='#888888'),
        xaxis=dict(
            range=[fromStrike, toStrike],
            tickvals=x_ticks,
            ticktext=x_labels,
            gridcolor='#444444',
            color='#888888',
            tickfont=dict(color='#888888')
        ),
        yaxis=dict(
            tickformat='$,.2f',
            gridcolor='#444444',
            color='#888888',
            tickfont=dict(color='#888888')
        ),
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(family='Arial', size=12, color='#888888'),
        width=1400,
        height=800,
        margin=dict(l=80, r=50, t=80, b=120),
        hovermode='x unified',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(0,0,0,0.7)',
            font=dict(color='#888888', size=11),
            bordercolor='#444444',
            borderwidth=1
        )
    )
    
    return fig

def calcular_gamma_profile_completo(df, spot):
    """
    Calcula o Gamma Profile completo com todas as curvas
    """
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("📐 Preparando dados para Gamma Profile...")
        progress_bar.progress(10)
        
        strikes_unicos = sorted(df['Strike'].unique())
        max_strikes = 500
        
        if len(strikes_unicos) > max_strikes:
            idx_spot = min(range(len(strikes_unicos)), key=lambda i: abs(strikes_unicos[i] - spot))
            half = max_strikes // 2
            start = max(0, idx_spot - half)
            end = min(len(strikes_unicos), idx_spot + half)
            strikes_limitados = strikes_unicos[start:end]
            status_text.text(f"📐 Limitando de {len(strikes_unicos)} para {len(strikes_limitados)} strikes...")
        else:
            strikes_limitados = strikes_unicos
        
        df_calc = df[df['Strike'].isin(strikes_limitados)].copy()
        
        status_text.text("📐 Calculando dias para expiração...")
        progress_bar.progress(30)
        
        hoje = datetime.now()
        df_calc['DaysToExpiry'] = (df_calc['ExpirationDate'] - hoje).dt.days
        df_calc['DaysToExpiry'] = df_calc['DaysToExpiry'].clip(lower=1)
        df_calc['T'] = df_calc['DaysToExpiry'] / 365.0
        
        status_text.text("📐 Identificando vencimentos...")
        progress_bar.progress(40)
        
        next_expiry = df_calc['ExpirationDate'].min()
        is_third_friday = (df_calc['ExpirationDate'].dt.weekday == 4) & (df_calc['ExpirationDate'].dt.day.between(15, 21))
        next_monthly = df_calc.loc[is_third_friday, 'ExpirationDate'].min()
        if pd.isna(next_monthly):
            next_monthly = next_expiry
        
        calls = df_calc[df_calc['Type'] == 'Call'].copy()
        puts = df_calc[df_calc['Type'] == 'Put'].copy()
        
        if calls.empty or puts.empty:
            status_text.text("❌ Dados insuficientes para cálculo")
            progress_bar.empty()
            status_text.empty()
            return None, None, None, None, None, None
        
        price_levels = np.linspace(0.85 * spot, 1.15 * spot, 30)
        
        status_text.text("📐 Calculando curvas Gamma...")
        progress_bar.progress(50)
        
        def calcular_gex(S, strikes, iv, oi, T):
            with np.errstate(divide='ignore', invalid='ignore'):
                sqrtT = np.sqrt(T)[np.newaxis, :]
                d1 = (np.log(S / strikes) + 0.5 * iv**2 * T) / (iv * sqrtT)
                gamma = norm.pdf(d1) / (S * iv * sqrtT)
                gamma = np.nan_to_num(gamma, nan=0.0, posinf=0.0, neginf=0.0)
                gex = gamma * oi * 100 * S**2 * 0.01
            return gex.sum(axis=1)
        
        S = price_levels[:, np.newaxis]
        
        status_text.text("📐 Curva: All Expiries...")
        progress_bar.progress(60)
        
        total_gex_call = calcular_gex(S, calls['Strike'].values, calls['IV'].fillna(0.3).values,
                                       calls['Open Interest'].values, calls['T'].values)
        total_gex_put = calcular_gex(S, puts['Strike'].values, puts['IV'].fillna(0.3).values,
                                      puts['Open Interest'].values, puts['T'].values)
        total_gamma = (total_gex_call - total_gex_put) / 1e9
        
        status_text.text("📐 Curva: Ex-Next Expiry...")
        progress_bar.progress(70)
        
        mask_next_call = calls['ExpirationDate'] != next_expiry
        mask_next_put = puts['ExpirationDate'] != next_expiry
        if mask_next_call.any() and mask_next_put.any():
            gex_call_next = calcular_gex(S, calls[mask_next_call]['Strike'].values,
                                          calls[mask_next_call]['IV'].fillna(0.3).values,
                                          calls[mask_next_call]['Open Interest'].values,
                                          calls[mask_next_call]['T'].values)
            gex_put_next = calcular_gex(S, puts[mask_next_put]['Strike'].values,
                                         puts[mask_next_put]['IV'].fillna(0.3).values,
                                         puts[mask_next_put]['Open Interest'].values,
                                         puts[mask_next_put]['T'].values)
            gamma_ex_next = (gex_call_next - gex_put_next) / 1e9
        else:
            gamma_ex_next = np.zeros_like(price_levels)
        
        status_text.text("📐 Curva: Ex-Next Monthly...")
        progress_bar.progress(80)
        
        mask_fri_call = (calls['ExpirationDate'] != next_expiry) & (calls['ExpirationDate'] != next_monthly)
        mask_fri_put = (puts['ExpirationDate'] != next_expiry) & (puts['ExpirationDate'] != next_monthly)
        if mask_fri_call.any() and mask_fri_put.any():
            gex_call_fri = calcular_gex(S, calls[mask_fri_call]['Strike'].values,
                                         calls[mask_fri_call]['IV'].fillna(0.3).values,
                                         calls[mask_fri_call]['Open Interest'].values,
                                         calls[mask_fri_call]['T'].values)
            gex_put_fri = calcular_gex(S, puts[mask_fri_put]['Strike'].values,
                                        puts[mask_fri_put]['IV'].fillna(0.3).values,
                                        puts[mask_fri_put]['Open Interest'].values,
                                        puts[mask_fri_put]['T'].values)
            gamma_ex_fri = (gex_call_fri - gex_put_fri) / 1e9
        else:
            gamma_ex_fri = np.zeros_like(price_levels)
        
        status_text.text("📐 Calculando Gamma Flip e Vol Trigger...")
        progress_bar.progress(90)
        
        gamma_flip = None
        zero_cross_idx = np.where(np.diff(np.sign(total_gamma)))[0]
        if len(zero_cross_idx) > 0:
            i = zero_cross_idx[0]
            x1, x2 = price_levels[i], price_levels[i+1]
            y1, y2 = total_gamma[i], total_gamma[i+1]
            if abs(y2 - y1) > 1e-10:
                gamma_flip = x1 - y1 * (x2 - x1) / (y2 - y1)
            else:
                gamma_flip = (x1 + x2) / 2
        
        vol_trigger = None
        if len(total_gamma) > 0:
            max_idx = np.argmax(total_gamma)
            min_idx = np.argmin(total_gamma)
            gamma_wall = price_levels[max_idx]
            gamma_risk = price_levels[min_idx]
            vol_trigger = gamma_wall - 0.75 * (gamma_wall - gamma_risk)
        
        progress_bar.progress(100)
        status_text.text("✅ Gamma Profile calculado!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        return price_levels, total_gamma, gamma_ex_next, gamma_ex_fri, gamma_flip, vol_trigger
        
    except Exception as e:
        st.error(f"Erro no cálculo do Gamma Profile: {str(e)}")
        return None, None, None, None, None, None
    
def criar_grafico_gamma_profile_curvas(price_levels, total_gamma, gamma_ex_next, gamma_ex_fri,
                                       spot, basis, gamma_flip=None, vol_trigger=None):
    """
    Cria o gráfico de curvas do Gamma Exposure Profile
    """
    fig = go.Figure()

    # Curva All Expiries
    fig.add_trace(go.Scatter(
        x=price_levels, y=total_gamma,
        mode='lines', 
        name='All Expiries',
        line=dict(color='#1f77b4', width=3.5),
        hovertemplate='Strike: %{x:.0f}<br>Gamma: %{y:.2f}<extra></extra>'
    ))

    # Curva Ex-Next Monthly
    fig.add_trace(go.Scatter(
        x=price_levels, y=gamma_ex_fri,
        mode='lines', 
        name='Ex-Next Monthly',
        line=dict(color='#2ca02c', width=1.8),
        hovertemplate='Strike: %{x:.0f}<br>Gamma: %{y:.2f}<extra></extra>'
    ))

    # Curva Ex-Next Expiry
    fig.add_trace(go.Scatter(
        x=price_levels, y=gamma_ex_next,
        mode='lines', 
        name='Ex-Next Expiry',
        line=dict(color='#ff7f0e', width=1.0),
        hovertemplate='Strike: %{x:.0f}<br>Gamma: %{y:.2f}<extra></extra>'
    ))

    # Linha do zero - CINZA
    fig.add_hline(y=0, line_dash="solid", line_color="#888888", opacity=0.5)

    # Linha do Spot - BRANCA
    spot_cvs = calcular_cvs(spot, basis, spot)
    fig.add_vline(x=spot, line_dash="dash", line_color="white", line_width=2,
                  annotation_text=f'SPOT {spot:.0f} ({spot_cvs:04d})',
                  annotation_position="top",
                  annotation_font=dict(color='white'))

    # Gamma Flip - VERDE
    if gamma_flip and not np.isnan(gamma_flip):
        gamma_flip_cvs = calcular_cvs(gamma_flip, basis, spot)
        fig.add_vline(x=gamma_flip, line_dash="dot", line_color="#2ca02c", line_width=2,
                      annotation_text=f'Gamma Flip {gamma_flip:.0f} ({gamma_flip_cvs:04d})',
                      annotation_position="bottom",
                      annotation_font=dict(color='#2ca02c'))

    # Vol Trigger - LARANJA
    if vol_trigger and not np.isnan(vol_trigger):
        vol_trigger_cvs = calcular_cvs(vol_trigger, basis, spot)
        fig.add_vline(x=vol_trigger, line_dash="dash", line_color="#ff7f0e", line_width=2,
                      annotation_text=f'Vol Trigger {vol_trigger:.0f} ({vol_trigger_cvs:04d})',
                      annotation_position="top left",
                      annotation_font=dict(color='#ff7f0e'))

    # Configuração do layout
    fig.update_layout(
        title=dict(text="📐 Gamma Exposure Profile", x=0.5, font=dict(size=20, color='#888888')),
        xaxis_title="Strike",
        xaxis_title_font=dict(color='#888888'),
        yaxis_title="Gamma Exposure (Bilhões/1%)",
        yaxis_title_font=dict(color='#888888'),
        plot_bgcolor='#2e2e2e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='#888888'),
        hovermode='x unified',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        height=600,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(0,0,0,0.7)',
            font=dict(color='#888888', size=11),
            bordercolor='#444444',
            borderwidth=1
        ),
        margin=dict(l=50, r=50, t=80, b=80)
    )

    # Configurar eixos - CINZA
    fig.update_xaxes(
        gridcolor='#444444', 
        tickangle=-45,
        zeroline=False,
        showline=True,
        linecolor='#888888',
        showgrid=True,
        gridwidth=0.5,
        mirror=False,
        tickfont=dict(color='#888888')
    )

    fig.update_yaxes(
        gridcolor='#444444',
        zeroline=True,
        zerolinecolor='#888888',
        zerolinewidth=1,
        showline=True,
        linecolor='#888888',
        showgrid=True,
        gridwidth=0.5,
        tickfont=dict(color='#888888')
    )

    # Formatar ticks do eixo X com CVS - CINZA
    n_ticks = min(15, len(price_levels))
    if len(price_levels) > n_ticks:
        tick_indices = np.linspace(0, len(price_levels) - 1, n_ticks, dtype=int)
        x_ticks = price_levels[tick_indices]
    else:
        x_ticks = price_levels

    x_labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in x_ticks]
    fig.update_xaxes(tickvals=x_ticks, ticktext=x_labels, tickfont=dict(size=10, color='#888888'))

    # Ajustar ticks do eixo Y automaticamente
    y_vals = []
    for trace in fig.data:
        if hasattr(trace, 'y') and trace.y is not None:
            y_vals.extend(trace.y)

    if y_vals:
        y_min = min(y_vals)
        y_max = max(y_vals)
        
        y_range = y_max - y_min
        if y_range > 0:
            y_min = y_min - y_range * 0.1
            y_max = y_max + y_range * 0.1
        else:
            y_min = -1
            y_max = 1
        
        range_size = y_max - y_min
        if range_size < 5:
            step = 0.5
        elif range_size < 20:
            step = 1.0
        elif range_size < 50:
            step = 2.0
        else:
            step = 5.0
        
        y_start = np.floor(y_min / step) * step
        y_end = np.ceil(y_max / step) * step
        y_ticks = np.arange(y_start, y_end + step, step)
        
        fig.update_yaxes(
            tickvals=y_ticks,
            tickformat='.1f',
            tickfont=dict(color='#888888'),
            range=[y_min, y_max]
        )
     
    # Range slider desabilitado
    fig.update_xaxes(
        rangeslider=dict(visible=False)
    )

    return fig

def criar_grafico_individual(strikes, pivots, spot, basis, metric, normalize=False):
    """
    Cria um gráfico individual para uma métrica específica
    """
    y_pos = list(range(len(strikes)))

    # ========== ADICIONADO: customdata com STRIKE e CVS para tooltip ==========
    cvs_values = [calcular_cvs(s, basis, spot) for s in strikes]
    custom_data = list(zip([int(s) for s in strikes], cvs_values))

    # Pegar os dados da métrica
    call_data = pivots[metric]["Call"].values.copy()
    put_data = pivots[metric]["Put"].values.copy()

    # Normalização se solicitada
    if normalize:
        max_val = max(abs(call_data).max(), abs(put_data).max(), 1)
        if max_val > 0:
            call_data = call_data / max_val * 100
            put_data = put_data / max_val * 100

    put_neg = [-abs(v) for v in put_data]

    # Cores personalizadas por métrica
    cores = {
        "DEX": {"call": "#FFFFFF", "put": "#FFFFFF", "nome": "Branco"},
        "GEX": {"call": "#00e5ff", "put": "#00e5ff", "nome": "Ciano"},
        "Open Interest": {"call": "#1d2fd4", "put": "#ff3333", "nome": "Azul Royal / Vermelho"},
        "Volume": {"call": "#888888", "put": "#888888", "nome": "Cinza"},
        "VANNA": {"call": "#FFFF00", "put": "#FF00FF", "nome": "Amarelo / Fúcsia"}
    }

    cor_call = cores.get(metric, {}).get("call", "#1f77b4")
    cor_put = cores.get(metric, {}).get("put", "#ff7f0e")

    # Títulos das métricas
    titulos = {
        "DEX": "📊 DEX - Delta Exposure",
        "GEX": "📈 GEX - Gamma Exposure",
        "Open Interest": "📊 Open Interest",
        "Volume": "📈 Volume",
        "VANNA": "📊 VANNA"
    }

    fig = go.Figure()

    # ========== MODIFICADO: hovertemplate mostra apenas STRIKE e CVS ==========
    hover_template = (
        "<b>STRIKE: %{customdata[0]}</b><br>"
        "<b>CVS: %{customdata[1]}</b>"
        "<extra></extra>"
    )

    # Barras Puts (negativas)
    fig.add_trace(go.Bar(
        y=y_pos,
        x=put_neg,
        orientation='h',
        name=f'{metric} Put',
        marker_color=cor_put,
        opacity=0.85,
        customdata=custom_data,
        hovertemplate=hover_template
    ))

    # Barras Calls (positivas)
    fig.add_trace(go.Bar(
        y=y_pos,
        x=call_data,
        orientation='h',
        name=f'{metric} Call',
        marker_color=cor_call,
        opacity=0.85,
        customdata=custom_data,
        hovertemplate=hover_template
    ))

    # Linha vertical do zero - CINZA
    fig.add_vline(x=0, line_width=1.5, line_dash="solid", line_color="#888888", opacity=0.7)

    # Rótulos dos strikes (com CVS) - CINZA
    labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in strikes]
    fig.update_yaxes(
        tickvals=y_pos,
        ticktext=labels,
        tickfont=dict(size=9, color='#888888')
    )

    # Linha do spot - BRANCA
    idx_spot = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot))
    spot_cvs = calcular_cvs(spot, basis, spot)
    spot_label = f'SPOT {spot:.0f} ({spot_cvs:04d})'

    fig.add_hline(
        y=idx_spot,
        line_dash="dash",
        line_color="white",
        line_width=2,
        opacity=0.8
    )

    # Anotação do spot - BRANCA
    fig.add_annotation(
        x=0.95,
        y=idx_spot,
        xref="x domain",
        yref="y",
        text=spot_label,
        showarrow=False,
        font=dict(size=10, color="white", weight="bold"),
        bgcolor="rgba(0,0,0,0.8)",
        bordercolor="#888888",
        borderwidth=0.5,
        borderpad=4
    )

    # Layout
    fig.update_layout(
        title=dict(
            text=titulos.get(metric, metric),
            x=0.5,
            font=dict(size=18, color='#888888')
        ),
        xaxis_title="Valor",
        xaxis_title_font=dict(color='#888888'),
        yaxis_title="Strike",
        yaxis_title_font=dict(color='#888888'),
        plot_bgcolor='#2e2e2e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='#888888'),
        height=700,
        barmode='overlay',
        hovermode='y unified',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        margin=dict(l=120, r=50, t=60, b=50),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(0,0,0,0.7)',
            font=dict(color='#888888', size=11),
            bordercolor='#444444',
            borderwidth=1
        )
    )

    # Configurar eixos - CINZA
    fig.update_xaxes(
        gridcolor='#444444',
        zeroline=False,
        showline=True,
        linecolor='#888888',
        tickfont=dict(color='#888888')
    )

    fig.update_yaxes(
        gridcolor='#444444',
        showline=True,
        linecolor='#888888',
        tickfont=dict(color='#888888')
    )

    return fig
def criar_grafico_todos_graficos(strikes, pivots, spot, basis, net_mode=False, normalize=False):
    """Cria 6 gráficos lado a lado (Todos os Gráficos) com as cores personalizadas"""
    y_pos = list(range(len(strikes)))

    # DEX
    dex_call = pivots["DEX"]["Call"].values.copy()
    dex_put = pivots["DEX"]["Put"].values.copy()

    # GEX
    gex_call = pivots["GEX"]["Call"].values.copy()
    gex_put = pivots["GEX"]["Put"].values.copy()

    # Open Interest
    oi_call = pivots["Open Interest"]["Call"].values.copy()
    oi_put = pivots["Open Interest"]["Put"].values.copy()

    # Volume
    vol_call = pivots["Volume"]["Call"].values.copy()
    vol_put = pivots["Volume"]["Put"].values.copy()

    # VANNA
    vanna_call = pivots["VANNA"]["Call"].values.copy()
    vanna_put = pivots["VANNA"]["Put"].values.copy()

    # Normalização se solicitada
    if normalize:
        for arr in [dex_call, dex_put, gex_call, gex_put, oi_call, oi_put, vol_call, vol_put, vanna_call, vanna_put]:
            max_val = max(abs(arr).max(), 1)
            if max_val > 0:
                arr[:] = arr / max_val * 100

    # Cores personalizadas
    COR_DEX = '#FFFFFF'
    COR_GEX = '#00e5ff'
    COR_OI_CALL = '#1d2fd4'
    COR_OI_PUT = '#ff3333'
    COR_VOL = '#888888'
    COR_VANNA_CALL = '#FFFF00'
    COR_VANNA_PUT = '#FF00FF'

    # Criar subplots: 2 linhas x 3 colunas
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=("DEX (Delta Exposure)", "GEX (Gamma Exposure)", 
                        "Open Interest", "Volume", "VANNA", " "),
        shared_xaxes=False,
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    # ========== 1. DEX ==========
    dex_put_neg = [-abs(v) for v in dex_put]
    fig.add_trace(go.Bar(
        y=y_pos, x=dex_put_neg, orientation='h', name='DEX Put',
        marker_color=COR_DEX, opacity=0.9, showlegend=False
    ), row=1, col=1)
    fig.add_trace(go.Bar( 
        y=y_pos, x=dex_call, orientation='h', name='DEX Call',
        marker_color=COR_DEX, opacity=0.9, showlegend=False
    ), row=1, col=1)

    # ========== 2. GEX ==========
    gex_put_neg = [-abs(v) for v in gex_put]
    fig.add_trace(go.Bar(
        y=y_pos, x=gex_put_neg, orientation='h', name='GEX Put',
        marker_color=COR_GEX, opacity=0.9, showlegend=False
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        y=y_pos, x=gex_call, orientation='h', name='GEX Call',
        marker_color=COR_GEX, opacity=0.9, showlegend=False
    ), row=1, col=2)

    # ========== 3. Open Interest ==========
    oi_put_neg = [-abs(v) for v in oi_put]
    fig.add_trace(go.Bar(
        y=y_pos, x=oi_put_neg, orientation='h', name='OI Put',
        marker_color=COR_OI_PUT, opacity=0.9, showlegend=False
    ), row=1, col=3)
    fig.add_trace(go.Bar(
        y=y_pos, x=oi_call, orientation='h', name='OI Call',
        marker_color=COR_OI_CALL, opacity=0.9, showlegend=False
    ), row=1, col=3)

    # ========== 4. Volume ==========
    vol_put_neg = [-abs(v) for v in vol_put]
    fig.add_trace(go.Bar(
        y=y_pos, x=vol_put_neg, orientation='h', name='Volume Put',
        marker_color=COR_VOL, opacity=0.8, showlegend=False
    ), row=2, col=1)
    fig.add_trace(go.Bar(
        y=y_pos, x=vol_call, orientation='h', name='Volume Call',
        marker_color=COR_VOL, opacity=0.8, showlegend=False
    ), row=2, col=1)

    # ========== 5. VANNA ==========
    vanna_put_neg = [-abs(v) for v in vanna_put]
    fig.add_trace(go.Bar(
        y=y_pos, x=vanna_put_neg, orientation='h', name='VANNA Put',
        marker_color=COR_VANNA_PUT, opacity=0.85, showlegend=False
    ), row=2, col=2)
    fig.add_trace(go.Bar(
        y=y_pos, x=vanna_call, orientation='h', name='VANNA Call',
        marker_color=COR_VANNA_CALL, opacity=0.85, showlegend=False
    ), row=2, col=2)

    # Linha vertical do zero em todos os subplots - CINZA
    for row in range(1, 3):
        for col in range(1, 4):
            if row == 2 and col == 3:
                continue
            fig.add_vline(x=0, line_width=1, line_dash="solid", line_color="#888888", 
                         opacity=0.5, row=row, col=col)

    # Rótulos dos strikes (com CVS) - CINZA
    labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in strikes]
    for row in range(1, 3):
        for col in range(1, 4):
            if row == 2 and col == 3:
                continue
            fig.update_yaxes(
                tickvals=y_pos,  
                ticktext=labels, 
                row=row, 
                col=col, 
                tickfont=dict(size=8, color='#888888')
            )

    # ========== LINHA DO SPOT EM TODOS OS GRÁFICOS ==========
    idx_spot = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot))
    spot_cvs = calcular_cvs(spot, basis, spot)
    spot_label = f'SPOT {spot:.0f} ({spot_cvs:04d})'

    subplots = [(1,1), (1,2), (1,3), (2,1), (2,2)]

    for row, col in subplots:
        fig.add_hline(
            y=idx_spot, 
            line_dash="dash", 
            line_color="white", 
            line_width=1.5, 
            opacity=0.8, 
            row=row, 
            col=col
        )
        
        fig.add_annotation(
            x=0.98,
            y=0.98,
            xref="x domain",
            yref="y domain",
            text=spot_label,
            showarrow=False,
            font=dict(size=9, color="white", weight="bold"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="#888888",
            borderwidth=0.5,
            borderpad=4,
            row=row,
            col=col
        )

    # ========== CONFIGURAR EIXOS X ==========
    for row in range(1, 3):
        for col in range(1, 4):
            if row == 2 and col == 3:
                continue
            fig.update_xaxes(
                title_text="Valor", 
                title_font=dict(color='#888888'),
                row=row, 
                col=col, 
                gridcolor='#444444',
                tickfont=dict(color='#888888')
            )

    # ========== LAYOUT FINAL ==========
    fig.update_layout(
        height=900,
        width=1200,
        plot_bgcolor='#2e2e2e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='#888888'),
        showlegend=False,
        hovermode='y unified',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        margin=dict(l=100, r=50, t=80, b=50)
    )

    # Configurar títulos dos subplots - CINZA
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(color='#888888', size=12)

    return fig


def criar_grafico_gamma_points(df, spot, basis, strikes, pivots, normalize=False):
    """
    Cria o gráfico Gamma Points - APENAS DEX (barras com altura dobrada)
    """
    # ========== PREPARAR DADOS ==========
    strikes = np.array(strikes)
    y_pos = np.arange(len(strikes))

    # Extrair dados do DEX
    dex_call = pivots["DEX"]["Call"].values
    dex_put = pivots["DEX"]["Put"].values

    # Normalização se solicitada
    if normalize:
        max_val = max(abs(dex_call).max(), abs(dex_put).max(), 1)
        if max_val > 0:
            dex_call = dex_call / max_val * 100
            dex_put = dex_put / max_val * 100

    # Puts vão para o lado negativo (esquerda)
    dex_put_neg = [-abs(v) for v in dex_put]

    # ========== CRIAR FIGURA ==========
    fig = go.Figure()

    # ========== DEX Puts (lado esquerdo - negativo) ==========
    fig.add_trace(go.Bar(
        y=y_pos,
        x=dex_put_neg,
        orientation='h',
        name='DEX Put',
        marker_color='white',
        opacity=0.85,
        width=1.5,
        hovertemplate='Strike: %{y}<br>DEX Put: %{x:.2f}<extra></extra>'
    ))

    # ========== DEX Calls (lado direito - positivo) ==========
    fig.add_trace(go.Bar(
        y=y_pos,
        x=dex_call,
        orientation='h',
        name='DEX Call',
        marker_color='white',
        opacity=0.85,
        width=1.5,
        hovertemplate='Strike: %{y}<br>DEX Call: %{x:.2f}<extra></extra>'
    ))

    # ========== LINHA DO ZERO ==========
    fig.add_vline(x=0, line_width=1.5, line_dash="solid", line_color="white", opacity=0.7)

    # ========== RÓTULOS DOS STRIKES (Y) ==========
    labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in strikes]
    fig.update_yaxes(
        tickvals=y_pos,
        ticktext=labels,
        tickfont=dict(size=9, color='white')
    )

    # ========== LINHA DO SPOT ==========
    idx_spot = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot))
    spot_cvs = calcular_cvs(spot, basis, spot)
    spot_label = f'SPOT {spot:.0f} ({spot_cvs:04d})'

    fig.add_hline(
        y=idx_spot,
        line_dash="dash",
        line_color="white",
        line_width=2,
        opacity=0.8
    )

    fig.add_annotation(
        x=0.95,
        y=idx_spot,
        xref="x domain",
        yref="y",
        text=spot_label,
        showarrow=False,
        font=dict(size=10, color="white", weight="bold"),
        bgcolor="rgba(0,0,0,0.8)",
        bordercolor="white",
        borderwidth=0.5,
        borderpad=4
    )

    # ========== LAYOUT ==========
    fig.update_layout(
        title=dict(
            text="📊 Gamma Points - DEX",
            x=0.5,
            font=dict(size=18, color='white')
        ),
        xaxis_title="Valor",
        xaxis_title_font=dict(color='white'),
        yaxis_title="Strike",
        yaxis_title_font=dict(color='white'),
        plot_bgcolor='#2e2e2e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='white'),
        height=700,
        barmode='overlay',
        hovermode='y unified',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        margin=dict(l=120, r=50, t=60, b=50),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor='rgba(0,0,0,0.7)',
            font=dict(color='white', size=11),
            bordercolor='#444444',
            borderwidth=1
        )
    )

    # ========== CONFIGURAR EIXOS ==========
    fig.update_xaxes(
        gridcolor='#444444',
        zeroline=False,
        showline=True,
        linecolor='#888888',
        tickfont=dict(color='white')
    )

    fig.update_yaxes( 
        gridcolor='#444444',
        showline=True,
        linecolor='#888888',
        tickfont=dict(color='white')
    )

    return fig

def criar_grafico_gamma_points_overlay(df, spot, basis, strikes, pivots, normalize=False,
                                       overlays=None, show_dex=True, show_gepls=False,
                                       gamma_profile_data=None,
                                       lines_pcp=None, lines_int=None):
    """
    🆕 VERSÃO COM LINHAS DE STRIKES (Pcp e Int)
    Gráfico Gamma Points com EIXOS X INDEPENDENTES
    - ✅ Tooltip mostra APENAS Strike e CVS (sem métricas)
    - ✅ hovermode='closest' - mostra apenas o trace mais próximo
    - ✅ Apenas DEX tem hover ativo, todos os outros são 'skip'
    - ✅ Sem linhas verticais de grade no eixo X
    - ✅ Cada métrica tem seu próprio eixo X com escala independente
    - ✅ Suporta zoom (scroll) e pan (arrastar)
    - ✅ 🟡 Linhas Pcp (amarelo tracejado) e Int (amarelo pontilhado) - largura 1
    """
    if overlays is None:
        overlays = []
    if lines_pcp is None:
        lines_pcp = []
    if lines_int is None:
        lines_int = []

    strikes = np.array(strikes)
    y_pos = strikes.copy()  # EIXO Y = VALORES REAIS DOS STRIKES
    n = len(strikes)

    # ========== CUSTOMDATA UNIFICADO (STRIKE + CVS) ==========
    cvs_values = [calcular_cvs(s, basis, spot) for s in strikes]
    custom_data = list(zip([int(s) for s in strikes], cvs_values))
    # ==========================================================

    # Calcular step médio dos strikes para ajustar altura das barras
    if n > 1:
        step_strikes = float(np.median(np.diff(strikes)))
    else:
        step_strikes = 1.0

    # Altura das barras proporcional ao step dos strikes
    bar_height = step_strikes * 0.8

    fig = go.Figure()

    # ========== FUNÇÃO AUXILIAR PARA CALCULAR RANGE ==========
    def get_range(data_call, data_put, margin=1.2):
        """Calcula range simétrico para um eixo X"""
        max_val = max(abs(data_call).max(), abs(data_put).max(), 1)
        return [-max_val * margin, max_val * margin]

    # ========== FUNÇÃO AUXILIAR PARA ADICIONAR OVERLAYS ==========
    def add_overlay(name, data_call, data_put, color_call, color_put, 
                    alpha=1.0, vazado=False, width_mult=0.6, xaxis_name='x2'):
        """Adiciona um overlay com seu próprio eixo X independente"""
        nonlocal fig
        
        if normalize:
            max_val = max(abs(data_call).max(), abs(data_put).max(), 1)
            if max_val > 0:
                data_call = data_call / max_val * 100
                data_put = data_put / max_val * 100
        
        data_put_neg = [-abs(v) for v in data_put]
        w = bar_height * width_mult
        
        if vazado:
            fig.add_trace(go.Bar(
                y=y_pos, x=data_put_neg, orientation='h',
                name=f'{name} Put', marker_color='rgba(0,0,0,0)',
                marker_line=dict(color=color_put, width=1.5),
                opacity=alpha, width=w, xaxis=xaxis_name,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Bar(
                y=y_pos, x=data_call, orientation='h',
                name=f'{name} Call', marker_color='rgba(0,0,0,0)',
                marker_line=dict(color=color_call, width=1.5),
                opacity=alpha, width=w, xaxis=xaxis_name,
                hoverinfo='skip'
            ))
        else:
            fig.add_trace(go.Bar(
                y=y_pos, x=data_put_neg, orientation='h',
                name=f'{name} Put', marker_color=color_put,
                opacity=alpha, width=w, xaxis=xaxis_name,
                hoverinfo='skip'
            ))
            fig.add_trace(go.Bar(
                y=y_pos, x=data_call, orientation='h',
                name=f'{name} Call', marker_color=color_call,
                opacity=alpha, width=w, xaxis=xaxis_name,
                hoverinfo='skip'
            ))
        
        return get_range(data_call, data_put)

    # ========== 1. DEX (BRANCO SÓLIDO) - Eixo X1 (principal) ==========
    ranges = {}

    if show_dex:
        dex_call = pivots["DEX"]["Call"].values.copy()
        dex_put = pivots["DEX"]["Put"].values.copy()
        
        if normalize:
            max_val = max(abs(dex_call).max(), abs(dex_put).max(), 1)
            if max_val > 0:
                dex_call = dex_call / max_val * 100
                dex_put = dex_put / max_val * 100
        
        dex_put_neg = [-abs(v) for v in dex_put]
        
        # ✅ Hovertemplate SIMPLIFICADO - SEM nome do trace, APENAS dados
        # <extra></extra> vazio remove completamente o nome do trace
        hover_unificado = (
            "STRIKE: <b>%{customdata[0]}</b><br>"
            "CVS: <b>%{customdata[1]}</b>"
            "<extra></extra>"
        )
        
        # ✅ DEX Put - trace com hover ativo
        fig.add_trace(go.Bar(
            y=y_pos, x=dex_put_neg, orientation='h',
            name='DEX Put', marker_color='white', opacity=0.9,
            width=bar_height, xaxis='x',
            customdata=custom_data,
            hovertemplate=hover_unificado,
            hoverinfo='text',
            # ✅ FORÇAR CORES DIRETAMENTE NO TRACE (parâmetros separados)
            hoverlabel_bgcolor='rgba(0, 0, 0, 0.95)',    # Fundo preto
            hoverlabel_bordercolor='#FFFF00',              # Borda amarela
            hoverlabel_font_color='white',                 # ✅ TEXTO BRANCO FORÇADO
            hoverlabel_font_size=14,                       # Fonte +2
            hoverlabel_font_family='Arial Black',          # Fonte grossa
            hoverlabel_namelength=0,                       # ✅ Remove nome do trace
            textfont=dict(color='white')                   # ✅ Força cor branca
        ))
        
        # ✅ DEX Call - trace com hover ativo
        fig.add_trace(go.Bar(
            y=y_pos, x=dex_call, orientation='h',
            name='DEX Call', marker_color='white', opacity=0.9,
            width=bar_height, xaxis='x',
            customdata=custom_data,
            hovertemplate=hover_unificado,
            hoverinfo='text',
            # ✅ FORÇAR CORES DIRETAMENTE NO TRACE (parâmetros separados)
            hoverlabel_bgcolor='rgba(0, 0, 0, 0.95)',    # Fundo preto
            hoverlabel_bordercolor='#FFFF00',              # Borda amarela
            hoverlabel_font_color='white',                 # ✅ TEXTO BRANCO FORÇADO
            hoverlabel_font_size=14,                       # Fonte +2
            hoverlabel_font_family='Arial Black',          # Fonte grossa
            hoverlabel_namelength=0,                       # ✅ Remove nome do trace
            textfont=dict(color='white')                   # ✅ Força cor branca
        ))
        
        ranges['x'] = get_range(dex_call, dex_put)
    else:
        ranges['x'] = [-10, 10]

    # ========== 2. OPEN INTEREST - Eixo X2 ==========
    if 'Open Interest' in overlays:
        ranges['x2'] = add_overlay('OI', 
                                    pivots["Open Interest"]["Call"].values.copy(),
                                    pivots["Open Interest"]["Put"].values.copy(),
                                    '#1d2fd4', '#ff3333', alpha=1.0, width_mult=0.5,
                                    xaxis_name='x2')

    # ========== 3. VOLUME - Eixo X3 ==========
    if 'Volume' in overlays:
        ranges['x3'] = add_overlay('Volume',
                                    pivots["Volume"]["Call"].values.copy(),
                                    pivots["Volume"]["Put"].values.copy(),
                                    '#888888', '#888888', alpha=0.5, width_mult=0.4,
                                    xaxis_name='x3')

    # ========== 4. VANNA (VAZADO) - Eixo X4 ==========
    if 'VANNA' in overlays:
        ranges['x4'] = add_overlay('VANNA',
                                    pivots["VANNA"]["Call"].values.copy(),
                                    pivots["VANNA"]["Put"].values.copy(),
                                    '#FFFF00', '#FF00FF', alpha=1.0, vazado=True, width_mult=0.8,
                                    xaxis_name='x4')

    # ========== 5. GEX - Eixo X5 ==========
    if 'GEX' in overlays:
        ranges['x5'] = add_overlay('GEX',
                                    pivots["GEX"]["Call"].values.copy(),
                                    pivots["GEX"]["Put"].values.copy(),
                                    '#1AF1F8', '#1AF1F8', alpha=0.85, width_mult=0.15,
                                    xaxis_name='x5')

    # ========== 6. GEPLS (CURVAS) - Eixo X6 ==========
    if show_gepls and gamma_profile_data:
        fig.add_trace(go.Scatter(
            x=gamma_profile_data['total_gamma'], 
            y=gamma_profile_data['price_levels'],
            mode='lines', name='GEPLS All Expiries',
            line=dict(color='#1f77b4', width=2.5),
            xaxis='x6',
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=gamma_profile_data['gamma_ex_next'], 
            y=gamma_profile_data['price_levels'],
            mode='lines', name='GEPLS Ex-Next Expiry',
            line=dict(color='#ff7f0e', width=1.5),
            xaxis='x6',
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=gamma_profile_data['gamma_ex_fri'], 
            y=gamma_profile_data['price_levels'],
            mode='lines', name='GEPLS Ex-Next Monthly',
            line=dict(color='#2ca02c', width=1.5),
            xaxis='x6',
            hoverinfo='skip'
        ))
        
        all_vals = np.concatenate([
            gamma_profile_data['total_gamma'],
            gamma_profile_data['gamma_ex_next'],
            gamma_profile_data['gamma_ex_fri']
        ])
        max_val = max(abs(all_vals).max(), 1)
        ranges['x6'] = [-max_val * 1.2, max_val * 1.2]

    # ========== 🟡 7. LINHAS DE STRIKES (Pcp e Int) - AMARELO ==========
    x_min_line = ranges.get('x', [-10, 10])[0]
    x_max_line = ranges.get('x', [-10, 10])[1]

    # 🟡 LINHAS Pcp - AMARELO TRACEJADO (dash), largura 1
    for strike in lines_pcp:
        cvs = calcular_cvs(strike, basis, spot)
        fig.add_hline(
            y=strike,
            line_dash="dash",        # ✅ TRACEJADA
            line_color="#FFFF00",    # Amarelo brilhante
            line_width=1,            # ✅ Largura 1
            opacity=1.0
        )
        fig.add_annotation(
            x=x_max_line,
            y=strike,
            xref="x",
            yref="y",
            text=f"  Pcp {int(strike)} ({cvs:04d})   ",
            showarrow=False,
            font=dict(size=10, color="white", family="Arial Black"),
            bgcolor="rgba(180, 180, 0, 0.85)",  # Fundo amarelo escuro
            bordercolor="#FFFF00",
            borderwidth=1,
            borderpad=3,
            xanchor="left"
        )

    # 🟡 LINHAS Int - AMARELO PONTILHADO (dot), largura 1
    for strike in lines_int:
        cvs = calcular_cvs(strike, basis, spot)
        fig.add_hline(
            y=strike,
            line_dash="dot",         # ✅ PONTILHADA
            line_color="#FFFF00",    # Amarelo brilhante
            line_width=1,            # ✅ Largura 1
            opacity=1.0
        )
        fig.add_annotation(
            x=x_min_line,
            y=strike,
            xref="x",
            yref="y",
            text=f"  Int {int(strike)} ({cvs:04d})   ",
            showarrow=False,
            font=dict(size=10, color="white", family="Arial Black"),
            bgcolor="rgba(180, 180, 0, 0.85)",  # Fundo amarelo escuro
            bordercolor="#FFFF00",
            borderwidth=1,
            borderpad=3,
            xanchor="right"
        )
    # =========================================================

    # ========== RÓTULOS DOS STRIKES (EIXO Y) ==========
    fontsize = max(8, min(11, 11 - n * 0.05))
    labels = [f"{int(s)}({calcular_cvs(s, basis, spot):04d})" for s in strikes]

    # ========== LINHA HORIZONTAL DO SPOT ==========
    spot_cvs = calcular_cvs(spot, basis, spot)
    spot_label = f'SPOT {spot:.0f} ({spot_cvs:04d})'

    fig.add_hline(y=spot, line_dash="dash", line_color="white", 
                  line_width=2, opacity=0.8)

    fig.add_annotation(
        x=0.98, y=spot, xref="x domain", yref="y",
        text=spot_label, showarrow=False,
        font=dict(size=10, color="white", family="Arial Black"),
        bgcolor="rgba(0,0,0,0.85)", bordercolor="#888888",
        borderwidth=1, borderpad=4
    )

    # ========== TÍTULO ==========
    overlay_text = ''
    if 'Volume' in overlays: overlay_text += ' + Volume'
    if 'Open Interest' in overlays: overlay_text += ' + OI'
    if 'VANNA' in overlays: overlay_text += ' + VANNA'
    if 'GEX' in overlays: overlay_text += ' + GEX'
    if show_gepls: overlay_text += ' + GEPLS'

    lines_info = ''
    if lines_pcp or lines_int:
        lines_info = f' | 🟡{len(lines_pcp)} Pcp 🟡{len(lines_int)} Int'

    title_text = f"Gamma Points - DEX{overlay_text}{lines_info}" if show_dex else f"Gamma Points{overlay_text}{lines_info}"
    if normalize:
        title_text += " (NORMALIZADO)"

    # ========== LAYOUT ==========
    height_fig = max(500, min(1200, n * 18))

    fig.update_layout(
        title=dict(text=title_text, x=0.5, 
                   font=dict(size=16, color='white', family='Arial Black')),
        xaxis_title='DEX' if show_dex else 'Valor',
        yaxis_title='Strike',
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='white', family='Arial', size=11),
        height=height_fig,
        barmode='overlay',
        hovermode='closest',
        # ⬇️ HOVER LABEL - FONTE +2 E BRANCO SÓLIDO ⬇️
        hoverlabel=dict(
            bgcolor='rgba(0, 0, 0, 0.85)',
            bordercolor='#888888',
            font=dict(size=14, color='white', family='Arial Black')
        ),
        # ⬆️ FIM DO BLOCO ⬆️
        margin=dict(l=130, r=50, t=70, b=60),
        legend=dict(
            orientation="v", yanchor="top", y=0.98,
            xanchor="right", x=0.99,
            bgcolor='rgba(0,0,0,0.7)',
            font=dict(color='white', size=9),
            bordercolor='#555555', borderwidth=1
        ),
        dragmode='pan',
    )
     
    # ========== EIXO Y (STRIKES REAIS - COMPARTILHADO) ==========
    fig.update_yaxes(
        tickvals=y_pos, ticktext=labels,
        tickfont=dict(size=fontsize, color='white'),
        gridcolor='#444444', gridwidth=0.5,
        showline=True, linecolor='white',
        range=[strikes.min() - step_strikes, strikes.max() + step_strikes],
        fixedrange=False
    ) 

    # ========== FUNÇÃO AUXILIAR PARA CRIAR EIXOS X ==========
    def make_xaxis_config(range_val, is_main=False):
        """Cria configuração para eixo X (principal ou overlay)"""
        return dict(
            range=range_val,
            overlaying='x' if not is_main else None,
            side='bottom' if is_main else 'top',
            showgrid=False,
            zeroline=False,
            showline=True if is_main else False,
            showticklabels=True if is_main else False,
            fixedrange=False,
            linecolor='white' if is_main else '#444444',
            tickfont=dict(color='white') if is_main else dict(color='#666666')
        )

    # ========== CONFIGURAR CADA EIXO X INDEPENDENTE ==========
    fig.update_layout(xaxis=make_xaxis_config(ranges.get('x', [-10, 10]), is_main=True))

    if 'x2' in ranges:
        fig.update_layout(xaxis2=make_xaxis_config(ranges['x2']))
    if 'x3' in ranges:
        fig.update_layout(xaxis3=make_xaxis_config(ranges['x3']))
    if 'x4' in ranges:
        fig.update_layout(xaxis4=make_xaxis_config(ranges['x4']))
    if 'x5' in ranges:
        fig.update_layout(xaxis5=make_xaxis_config(ranges['x5']))
    if 'x6' in ranges:
        fig.update_layout(xaxis6=make_xaxis_config(ranges['x6']))

    return fig
#=======================================================
# DOWNLOAD AUTOMÁTICO
# =============================================================================

def baixar_planilha_api(simbolo="SPX", pasta_destino=None):
    """Baixa dados da CBOE via API pública"""
    if pasta_destino is None:
        pasta_destino = os.path.join("downloads", "CBOE")
    os.makedirs(pasta_destino, exist_ok=True)

    def extrair_strike(opt_code):
        return int(opt_code[-8:]) / 1000
    def extrair_tipo(opt_code):
        return opt_code[-9]
    def extrair_data_vencimento(opt_code):
        d = opt_code[-15:-9]
        return datetime(2000+int(d[:2]), int(d[2:4]), int(d[4:6])).strftime("%a %b %d %Y")
    def extrair_data_ordenavel(opt_code):
        d = opt_code[-15:-9]
        return f"20{d[:2]}-{d[2:4]}-{d[4:6]}"

    def obter_dados_ativo(sym):
        headers = {'User-Agent': 'Mozilla/5.0'}
        urls = [f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{sym}.json",
                f"https://cdn.cboe.com/api/global/delayed_quotes/{sym}.json"]
        for url in urls:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    q = r.json().get('data', r.json())
                    last = q.get('current_price') or q.get('last')
                    if last and float(last) > 0:
                        return (f"{float(last):.2f}",
                                f"{float(q.get('price_change') or 0):.2f}",
                                f"{float(q.get('bid') or 0):.2f}",
                                f"{float(q.get('ask') or 0):.2f}",
                                f"{int(q.get('volume') or 0):,}".replace(",", "."),
                                f"{int(q.get('bid_size') or 1)}*{int(q.get('ask_size') or 1)}")
            except:
                pass
        raise Exception(f"Falha ao obter dados para {sym}")

    urls_opts = [f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{simbolo}.json",
                f"https://cdn.cboe.com/api/global/delayed_quotes/options/{simbolo}.json"]
    dados = None
    for url in urls_opts:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if r.status_code == 200:
                dados = r.json()
                break
        except:
            pass
    if not dados or 'options' not in dados.get('data', {}):
        return None

    df = pd.DataFrame(dados['data']['options'])
    divisor = 1000 if simbolo == "SPX" else 1
    if 'strike' in df.columns:
        df['strike'] = pd.to_numeric(df['strike'], errors='coerce')
        if divisor != 1:
            df['strike'] /= divisor
    else:
        df['strike'] = df['option'].apply(extrair_strike)

    if 'option_type' in df.columns:
        df['tipo'] = df['option_type'].str.upper().str[0]
    else:
        df['tipo'] = df['option'].apply(extrair_tipo)

    df['expiration'] = df['option'].apply(extrair_data_vencimento)
    df['expiration_sort'] = df['option'].apply(extrair_data_ordenavel)

    calls = df[df['tipo'] == 'C'].copy()
    puts = df[df['tipo'] == 'P'].copy()

    call_cols = {'option': 'Calls', 'last_trade_price': 'Call_Last_Sale', 'change': 'Call_Net',
                'bid': 'Call_Bid', 'ask': 'Call_Ask', 'volume': 'Call_Volume', 'iv': 'Call_IV',
                'delta': 'Call_Delta', 'gamma': 'Call_Gamma', 'open_interest': 'Call_Open_Interest'}
    put_cols = {'option': 'Puts', 'last_trade_price': 'Put_Last_Sale', 'change': 'Put_Net',
                'bid': 'Put_Bid', 'ask': 'Put_Ask', 'volume': 'Put_Volume', 'iv': 'Put_IV',
                'delta': 'Put_Delta', 'gamma': 'Put_Gamma', 'open_interest': 'Put_Open_Interest'}

    for c in list(call_cols) + list(put_cols):
        if c not in df.columns:
            df[c] = ''

    calls = calls[list(call_cols) + ['strike', 'expiration', 'expiration_sort']].rename(columns=call_cols)
    puts = puts[list(put_cols) + ['strike', 'expiration', 'expiration_sort']].rename(columns=put_cols)

    cross = pd.merge(calls, puts, on=['expiration_sort', 'strike'], how='outer', suffixes=('_call', '_put'))
    cross['expiration'] = cross['expiration_call'].fillna(cross['expiration_put'])
    cross.drop(columns=['expiration_call', 'expiration_put', 'expiration_sort'], inplace=True)
    cross.dropna(how='all', inplace=True)

    try:
        last_price, change_price, bid_val, ask_val, volume_val, size_str = obter_dados_ativo(simbolo)
    except Exception as e:
        return None

    nome = {"SPX": "S&P 500 INDEX", "NDX": "NASDAQ 100 INDEX"}.get(simbolo, f"{simbolo} INDEX")
    now = datetime.now()
    data_hora = now.strftime("%d de %B de %Y às %H:%M GMT-4")
    meses_pt = {'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
                'April': 'abril', 'May': 'maio', 'June': 'junho', 'July': 'julho',
                'August': 'agosto', 'September': 'setembro', 'October': 'outubro',
                'November': 'novembro', 'December': 'dezembro'}
    for en, pt in meses_pt.items():
        data_hora = data_hora.replace(en, pt)

    cabecalho = ("Expiration Date,Calls,Last Sale,Net,Bid,Ask,Volume,IV,Delta,Gamma,Open Interest,Strike,"
                "Puts,Last Sale,Net,Bid,Ask,Volume,IV,Delta,Gamma,Open Interest")

    call_f = cross[['expiration', 'Calls', 'Call_Last_Sale', 'Call_Net', 'Call_Bid', 'Call_Ask',
                    'Call_Volume', 'Call_IV', 'Call_Delta', 'Call_Gamma', 'Call_Open_Interest', 'strike']].copy()
    put_f = cross[['expiration', 'Puts', 'Put_Last_Sale', 'Put_Net', 'Put_Bid', 'Put_Ask',
                'Put_Volume', 'Put_IV', 'Put_Delta', 'Put_Gamma', 'Put_Open_Interest', 'strike']].copy()
    call_f.columns = ['Expiration Date', 'Calls', 'Last Sale', 'Net', 'Bid', 'Ask',
                    'Volume', 'IV', 'Delta', 'Gamma', 'Open Interest', 'Strike']
    put_f.columns = ['Expiration Date', 'Puts', 'Last Sale', 'Net', 'Bid', 'Ask',
                    'Volume', 'IV', 'Delta', 'Gamma', 'Open Interest', 'Strike']

    export_df = pd.merge(call_f, put_f, on=['Expiration Date', 'Strike'], how='outer', suffixes=('_call', '_put'))

    num_cols = export_df.select_dtypes(include=['float64', 'int64']).columns
    export_df[num_cols] = export_df[num_cols].round(4)
    export_df = export_df.drop_duplicates(keep='first')
    export_df['Date_Sort'] = pd.to_datetime(export_df['Expiration Date'], format='%a %b %d %Y', errors='coerce')
    export_df = export_df.sort_values(by=['Date_Sort', 'Strike'], ascending=[True, True]).reset_index(drop=True)
    export_df['Expiration Date'] = export_df['Date_Sort'].dt.strftime('%a %b %d %Y')
    export_df.drop(columns=['Date_Sort'], inplace=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arq = f"{simbolo.lower()}_quotedata_{timestamp}.csv"
    caminho = os.path.join(pasta_destino, nome_arq)

    with open(caminho, 'w', encoding='utf-8-sig', newline='') as f:
        f.write("\n")
        f.write(f"{nome},Last: {last_price},Change:  {change_price}\n")
        f.write(f"Date: {data_hora},Bid: {bid_val},Ask: {ask_val},Size: {size_str},Volume: {volume_val}\n")
        f.write(cabecalho + "\n")
        w = csv.writer(f, lineterminator='\n')
        for _, r in export_df.iterrows():
            w.writerow([
                r['Expiration Date'], r['Calls'], r['Last Sale_call'], r['Net_call'],
                r['Bid_call'], r['Ask_call'], r['Volume_call'], r['IV_call'],
                r['Delta_call'], r['Gamma_call'], r['Open Interest_call'], r['Strike'],
                r['Puts'], r['Last Sale_put'], r['Net_put'], r['Bid_put'], r['Ask_put'],
                r['Volume_put'], r['IV_put'], r['Delta_put'], r['Gamma_put'], r['Open Interest_put']
            ])

    latest = os.path.join(pasta_destino, f"{simbolo.lower()}_quotedata_latest.csv")
    if os.path.exists(latest):
        os.remove(latest)
    shutil.copy2(caminho, latest)
    return latest


def baixar_planilha_yahoo(simbolo, pasta_destino=None):
    """Baixa dados via Yahoo Finance"""
    import yfinance as yf
    
    if pasta_destino is None:
        pasta_destino = os.path.join("downloads", "YAHOO")
    os.makedirs(pasta_destino, exist_ok=True)

    ticker = yf.Ticker(simbolo)
    info = ticker.info
    spot = info.get('regularMarketPrice') or info.get('currentPrice')
    if not spot or spot <= 0:
        hist = ticker.history(period='1d')
        if not hist.empty:
            spot = hist['Close'].iloc[-1]
    if not spot or spot <= 0:
        return None

    expirations = ticker.options
    if not expirations:
        return None

    all_calls, all_puts = [], []
    for exp_date in expirations:
        try:
            opt = ticker.option_chain(exp_date)
            calls = opt.calls
            puts = opt.puts
            calls['expiration'] = exp_date
            puts['expiration'] = exp_date
            all_calls.append(calls)
            all_puts.append(puts)
        except Exception as e:
            pass

    if not all_calls:
        return None

    calls_df = pd.concat(all_calls, ignore_index=True)
    puts_df = pd.concat(all_puts, ignore_index=True)

    def padronizar(df, tipo):
        mapping = {
            'strike': 'Strike', 'lastPrice': 'Last_Sale', 'bid': 'Bid', 'ask': 'Ask',
            'volume': 'Volume', 'openInterest': 'Open_Interest', 'impliedVolatility': 'IV',
            'delta': 'Delta', 'gamma': 'Gamma'
        }
        df = df.rename(columns=mapping)
        for col in ['Strike', 'Last_Sale', 'Bid', 'Ask', 'Volume', 'Open_Interest', 'IV', 'Delta', 'Gamma']:
            if col not in df.columns:
                df[col] = 0.0
        df['Net'] = 0
        df['Type'] = tipo
        df['ExpirationDate'] = pd.to_datetime(df['expiration']).dt.strftime('%a %b %d %Y')
        return df[['ExpirationDate', 'Strike', 'Last_Sale', 'Net', 'Bid', 'Ask', 'Volume', 'IV', 'Delta', 'Gamma', 'Open_Interest', 'Type']]

    calls_long = padronizar(calls_df, 'Call')
    puts_long = padronizar(puts_df, 'Put')

    calls_wide = calls_long.drop(columns=['Type']).rename(columns={
        'Last_Sale': 'Call_Last_Sale', 'Net': 'Call_Net', 'Bid': 'Call_Bid', 'Ask': 'Call_Ask',
        'Volume': 'Call_Volume', 'IV': 'Call_IV', 'Delta': 'Call_Delta', 'Gamma': 'Call_Gamma',
        'Open_Interest': 'Call_Open_Interest'
    })
    puts_wide = puts_long.drop(columns=['Type']).rename(columns={
        'Last_Sale': 'Put_Last_Sale', 'Net': 'Put_Net', 'Bid': 'Put_Bid', 'Ask': 'Put_Ask',
        'Volume': 'Put_Volume', 'IV': 'Put_IV', 'Delta': 'Put_Delta', 'Gamma': 'Put_Gamma',
        'Open_Interest': 'Put_Open_Interest'
    })

    merged = pd.merge(calls_wide, puts_wide, on=['ExpirationDate', 'Strike'], how='outer').fillna(0)
    merged['Calls'] = ''
    merged['Puts'] = ''
    merged['CallSymbol'] = ''
    merged['PutSymbol'] = ''
    merged = merged.sort_values(['ExpirationDate', 'Strike'])

    nome_empresa = info.get('longName', f'{simbolo} INDEX')
    change = info.get('regularMarketChange', 0.0)
    bid = info.get('bid', 0.0)
    ask = info.get('ask', 0.0)
    volume = info.get('volume', 0)
    size_str = f"{info.get('bidSize', 1)}*{info.get('askSize', 1)}"
    data_hora = datetime.now().strftime("%d de %B de %Y às %H:%M GMT-4")
    meses_pt = {'January': 'janeiro', 'February': 'fevereiro', 'March': 'março',
                'April': 'abril', 'May': 'maio', 'June': 'junho', 'July': 'julho',
                'August': 'agosto', 'September': 'setembro', 'October': 'outubro',
                'November': 'novembro', 'December': 'dezembro'}
    for en, pt in meses_pt.items():
        data_hora = data_hora.replace(en, pt)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arq = f"{simbolo.lower()}_quotedata_{timestamp}.csv"
    caminho = os.path.join(pasta_destino, nome_arq)

    with open(caminho, 'w', encoding='utf-8-sig', newline='') as f:
        f.write("\n")
        f.write(f"{nome_empresa},Last: {spot:.3f},Change:  {change:.3f}\n")
        f.write(f"Date: {data_hora},Bid: {bid:.2f},Ask: {ask:.2f},Size: {size_str},Volume: {volume}\n")
        f.write("Expiration Date,Calls,Last Sale,Net,Bid,Ask,Volume,IV,Delta,Gamma,Open Interest,Strike,Puts,Last Sale,Net,Bid,Ask,Volume,IV,Delta,Gamma,Open Interest\n")
        writer = csv.writer(f, lineterminator='\n')
        for _, row in merged.iterrows():
            writer.writerow([
                row['ExpirationDate'], row['Calls'], row['Call_Last_Sale'], row['Call_Net'],
                row['Call_Bid'], row['Call_Ask'], row['Call_Volume'], row['Call_IV'],
                row['Call_Delta'], row['Call_Gamma'], row['Call_Open_Interest'], row['Strike'],
                row['Puts'], row['Put_Last_Sale'], row['Put_Net'], row['Put_Bid'], row['Put_Ask'],
                row['Put_Volume'], row['Put_IV'], row['Put_Delta'], row['Put_Gamma'], row['Put_Open_Interest']
            ])

    latest = os.path.join(pasta_destino, f"{simbolo.lower()}_quotedata_latest.csv")
    if os.path.exists(latest):
        os.remove(latest)
    shutil.copy2(caminho, latest)
    return latest


def baixar_spx_completo_sem_thread(pasta_base="downloads"):
    """Baixa SPX + ativos de apoio"""
    import streamlit as st
    
    pasta_heatmap = os.path.join(pasta_base, "HEATMAP_SPX")
    pasta_cboe = os.path.join(pasta_heatmap, "CBOE")
    pasta_yahoo = os.path.join(pasta_heatmap, "YAHOO")
    
    os.makedirs(pasta_cboe, exist_ok=True)
    os.makedirs(pasta_yahoo, exist_ok=True)
    
    ativos_cboe = ["SPX", "NDX"]
    ativos_yahoo = ["EWZ", "VALE", "PBR", "SPY", "USO", "EEM", "ABEV", "ITUB"]
    
    resultados = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total = len(ativos_cboe) + len(ativos_yahoo)
    idx = 0
    
    for ativo in ativos_cboe:
        status_text.text(f"🔄 Baixando {ativo} via CBOE API...")
        caminho = baixar_planilha_api(ativo, pasta_cboe)
        resultados[ativo] = caminho
        idx += 1
        progress_bar.progress(idx / total)
        time.sleep(1)
    
    for ativo in ativos_yahoo:
        status_text.text(f"🔄 Baixando {ativo} via Yahoo Finance...")
        caminho = baixar_planilha_yahoo(ativo, pasta_yahoo)
        resultados[ativo] = caminho
        idx += 1
        progress_bar.progress(idx / total)
        time.sleep(1)
    
    status_text.text("✅ Download concluído!")
    progress_bar.progress(100)
    time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    return resultados, pasta_heatmap


def iniciar_download_spx_completo():
    """Inicia o download completo"""
    import streamlit as st
    
    if st.session_state.get("download_em_andamento", False):
        st.warning("⏳ Um download já está em andamento. Aguarde...")
        return
    
    st.session_state["download_em_andamento"] = True
    
    try:
        resultados, pasta = baixar_spx_completo_sem_thread("downloads")
        st.session_state["download_resultados"] = resultados
        st.session_state["download_pasta"] = pasta
        st.success("✅ Download concluído! Recarregue a página para visualizar os arquivos.")
        
        with st.expander("📋 Resultados do Download"):
            for ativo, caminho in resultados.items():
                if caminho:
                    st.success(f"✅ {ativo}: {os.path.basename(caminho)}")
                else:
                    st.error(f"❌ {ativo}: Falha no download")
        
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro durante o download: {str(e)}")
    finally:
        st.session_state["download_em_andamento"] = False


def abrir_dialogo_download_manual():
    """Abre um diálogo para download manual de um ativo específico"""
    with st.form("download_manual_form"):
        st.subheader("📥 Download Manual")
        
        ativo = st.text_input("Código do Ativo", value="SPX", help="Ex: SPX, EWZ, VALE, AAPL, MSFT")
        
        fonte = st.radio(
            "Fonte",
            options=["Auto", "CBOE", "Yahoo"],
            horizontal=True,
            help="Auto: SPX/NDX usa CBOE, outros usam Yahoo"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📥 Baixar", use_container_width=True, type="primary")
        with col2:
            if st.form_submit_button("Cancelar", use_container_width=True):
                st.rerun()
        
        if submitted:
            if not ativo.strip():
                st.error("Digite um código de ativo válido.")
                return
            
            ativo = ativo.strip().upper()
            
            with st.spinner(f"Baixando {ativo}..."):
                if fonte == "CBOE" or (fonte == "Auto" and ativo in ["SPX", "NDX"]):
                    pasta = os.path.join("downloads", "CBOE")
                    os.makedirs(pasta, exist_ok=True)
                    caminho = baixar_planilha_api(ativo, pasta)
                else:
                    pasta = os.path.join("downloads", "YAHOO")
                    os.makedirs(pasta, exist_ok=True)
                    caminho = baixar_planilha_yahoo(ativo, pasta)
            
            if caminho and os.path.exists(caminho):
                st.success(f"✅ {ativo} baixado com sucesso!")
                st.info(f"📁 Arquivo salvo em: {caminho}")
                
                if st.button("📂 Carregar este arquivo agora", use_container_width=True):
                    st.session_state["arquivo_para_carregar"] = caminho
                    st.rerun()
            else:
                st.error(f"❌ Falha ao baixar {ativo}. Verifique o código e tente novamente.")

# =============================================================================
# REL A1
# =============================================================================
def gerar_relatorio_a1_streamlit(df, spot, basis, symbol, active_expiry_filter, strikes, pivots):
    """
    Gera o relatório A1 completo no Streamlit com formatação 4 dígitos
    """
    import re
    from datetime import datetime
    import numpy as np
    
    # ========== 1. VALIDAÇÃO DO BASIS ==========
    if abs(basis - 1.0) < 1e-6:
        return "⚠️ BASIS OF CONVERSION deve ser diferente de 1 para gerar o relatório."
    
    if df is None or df.empty:
        return f"⚠️ Nenhum dado encontrado para o filtro: {active_expiry_filter}"
    
    # ========== 2. MODO DE EXPIRAÇÃO ==========
    mode_map = {
        None: "ALL",
        "ALL Expiry": "ALL",
        "MONTH Expiry": "MONTH",
        "0DTE + 4 Expiry": "ZERO_DTE_PLUS_4",
        "0DTE Expiry": "ZERO_DTE",
        "0DTE +1 Plus Friday": "ZERO_DTE_PLUS_NEXT_FRIDAY",
        "0DTE Expiry +1": "ZERO_DTE_PLUS_ONE"
    }
    mode = mode_map.get(active_expiry_filter, "ALL")
    
    data_str = datetime.now().strftime('%d/%m/%Y')
    modo_texto = {
        'ALL': 'TODOS (Todos os vencimentos)',
        'ZERO_DTE': 'ZERO DTE',
        'MONTH': 'MENSAL (Terceira sexta-feira)',
        'ZERO_DTE_PLUS_ONE': 'ZERO DTE + PRÓXIMO',
        'ZERO_DTE_PLUS_NEXT_FRIDAY': '0DTE +1 Plus Friday',
        'ZERO_DTE_PLUS_4': '0DTE + 4 PROXIMOS VENCIMENTOS'
    }.get(mode, mode)
    
    ratio = basis / spot if spot != 0 else 1.0
    
    # ========== 3. CALCULAR MÉTRICAS ==========
    metrics = calcular_metricas_a1(df, spot, basis, strikes, pivots)
    
    # ========== 4. FORMATAR RELATÓRIO (COM 4 DÍGITOS) ==========
    linhas = []
    
    # Cabeçalho
    linhas.append(f"ANALISE REALIZADA: EM {data_str}")
    linhas.append("")
    linhas.append(f"MODO DE EXPIRAÇÃO: {modo_texto}")
    linhas.append("")
    linhas.append(f"BASIS_OF_CONVERSION_D1\t({basis:.2f});")
    linhas.append(f"CLOSE_SPOT_D1\t({spot:.2f});")
    linhas.append("")
    
    # CW1_HW a CW20 (4 dígitos)
    for i in range(1, 21):
        nome = f"CW{i}" if i > 1 else "CW1_HW"
        valor = int(metrics.get(nome, 0))
        linhas.append(f"{nome}\t({valor:04d});")
    
    linhas.append("")
    
    # PW1_LP a PW20 (4 dígitos)
    for i in range(1, 21):
        nome = f"PW{i}" if i > 1 else "PW1_LP"
        valor = int(metrics.get(nome, 0))
        linhas.append(f"{nome}\t({valor:04d});")
    
    linhas.append("")
    
    # Point_I1 a Point_I20 (4 dígitos)
    for i in range(1, 21):
        valor = int(metrics.get(f'Point_I{i}', 0))
        linhas.append(f"Point_I{i}\t({valor:04d});")
    
    linhas.append("")
    
    # Gamma Flip (4 dígitos)
    linhas.append(f"GamaFlip_A\t({int(metrics.get('GamaFlip_A', 0)):04d});")
    linhas.append(f"GamaFlip_B\t({int(metrics.get('GamaFlip_B', 0)):04d});")
    linhas.append(f"GamaFlip_C\t({int(metrics.get('GamaFlip_C', 0)):04d});")
    linhas.append("")
    
    # Vol Trigger (4 dígitos)
    for letra in ['A', 'B', 'C', 'D']:
        linhas.append(f"Vol_Trigger{letra}\t({int(metrics.get(f'Vol_Trigger{letra}', 0)):04d});")
    
    linhas.append("")
    
    # Max/Min por expiração (4 dígitos)
    linhas.append(f"Max_CW_0DTE\t({int(metrics.get('Max_CW_0DTE', 0)):04d});")
    linhas.append(f"Min_PW_0DTE\t({int(metrics.get('Min_PW_0DTE', 0)):04d});")
    linhas.append(f"Max_CW_MONTH\t({int(metrics.get('Max_CW_MONTH', 0)):04d});")
    linhas.append(f"Min_PW_MONTH\t({int(metrics.get('Min_PW_MONTH', 0)):04d});")
    linhas.append(f"Max_CW_ALL\t({int(metrics.get('Max_CW_ALL', 0)):04d});")
    linhas.append(f"Min_PW_ALL\t({int(metrics.get('Min_PW_ALL', 0)):04d});")
    linhas.append("")
    
    # MAX_PAIN e NET_VANNA (4 dígitos)
    linhas.append(f"MAX_PAIN\t({int(metrics.get('MAX_PAIN', 0)):04d});")
    linhas.append(f"NET_VANNA\t({int(metrics.get('NET_VANNA', 0)):04d});")
    linhas.append("")
    
    # BN_1 a BN_12 (4 dígitos)
    for i in range(1, 13):
        linhas.append(f"BN_{i}\t({int(metrics.get(f'BN_{i}', 0)):04d});")
    
    linhas.append("")
    
    # Métricas Delta (4 dígitos)
    delta_fields = ['Delta_S1','Delta_S2','Delta_S3','Delta_R1','Delta_R2','Delta_R3',
                    'Delta_Flip','Delta_T_UP','Delta_T_DOWN','Delta_Max_Buy','Delta_Max_Sell',
                    'GVC_Strike','DNB_Low','DNB_High']
    for f in delta_fields:
        linhas.append(f"{f}\t({int(metrics.get(f, 0)):04d});")
    
    linhas.append("")
    
    # Delta_NZ (float)
    linhas.append(f"Delta_NZ\t({metrics.get('Delta_NZ', 0):.2f});")
    linhas.append("")
    
    # Delta Acceleration (4 dígitos)
    linhas.append(f"Delta_AC1_Buy\t({int(metrics.get('Delta_AC1_Buy', 0)):04d});")
    linhas.append(f"Delta_AC1_Sell\t({int(metrics.get('Delta_AC1_Sell', 0)):04d});")
    linhas.append(f"Delta_AC2_Buy\t({int(metrics.get('Delta_AC2_Buy', 0)):04d});")
    linhas.append(f"Delta_AC2_Sell\t({int(metrics.get('Delta_AC2_Sell', 0)):04d});")
    linhas.append("")
    
    # GFS e PCOR (float)
    linhas.append(f"GFS\t({metrics.get('GFS', 0):.2f});")
    linhas.append(f"PCOR\t({metrics.get('PCOR', 0):.2f});")
    linhas.append("")
    
    # COMPRA e VENDA (4 dígitos)
    for i in range(1, 5):
        linhas.append(f"COMPRA{i}\t({int(metrics.get(f'COMPRA{i}', 0)):04d});")
    for i in range(1, 5):
        linhas.append(f"VENDA{i}\t({int(metrics.get(f'VENDA{i}', 0)):04d});")
    linhas.append("")
    
    # Vol_Attack e A_Zero (4 dígitos)
    linhas.append(f"Vol_Attack\t({int(metrics.get('Vol_Attack', 0)):04d});")
    linhas.append(f"A_Zero\t({int(metrics.get('A_Zero', 0)):04d});")
    linhas.append("")
    
    # Action Points (4 dígitos)
    for i in range(1, 11):
        linhas.append(f"ACT_P{i}_CW\t({int(metrics.get(f'ACT_P{i}_CW', 0)):04d});")
    for i in range(1, 11):
        linhas.append(f"ACT_P{i}_PW\t({int(metrics.get(f'ACT_P{i}_PW', 0)):04d});")
    
    # Rodapé
    linhas.append("")
    linhas.append("")
    linhas.append(f"✅ CONVERSÃO APLICADA: ratio = {ratio:.4f} (winfut/asset)")
    linhas.append(f"✅ SPOT USADO: {spot:.2f} (AUTOMÁTICO)")
    linhas.append(f"✅ BASIS USADO: {basis:.2f}")
    
    return "\n".join(linhas)

def calcular_metricas_a1(df, spot, basis, strikes, pivots):
    """
    Calcula todas as métricas para o relatório A1
    COM VALIDAÇÃO PARA EVITAR None
    """
    import numpy as np
    from datetime import datetime
    
    metrics = {}
    
    # ========== VALIDAÇÕES INICIAIS ==========
    if strikes is None or len(strikes) == 0:
        return metrics
    
    if pivots is None or len(pivots) == 0:
        return metrics
    
    # ========== 1. GEX e Call/Put Walls ==========
    try:
        gex_call = pivots["GEX"]["Call"].values
        gex_put = pivots["GEX"]["Put"].values
        gex_net = gex_call - gex_put
    except (KeyError, AttributeError, TypeError):
        gex_call = np.zeros(len(strikes))
        gex_put = np.zeros(len(strikes))
        gex_net = np.zeros(len(strikes))
    
    # ========== 2. CW1_HW a CW20 ==========
    cw_strikes = []
    if len(gex_net) > 0 and len(strikes) > 0:
        pos_gex = [(strikes[i], gex_net[i]) for i in range(len(strikes)) if gex_net[i] > 0]
        pos_gex.sort(key=lambda x: x[1], reverse=True)
        cw_strikes = [int(x[0]) for x in pos_gex[:20]]
    
    while len(cw_strikes) < 20:
        cw_strikes.append(0)
    
    for i in range(20):
        nome = f"CW{i+1}" if i > 0 else "CW1_HW"
        metrics[nome] = cw_strikes[i] if i < len(cw_strikes) else 0
    
    # ========== 3. PW1_LP a PW20 ==========
    pw_strikes = []
    if len(gex_net) > 0 and len(strikes) > 0:
        neg_gex = [(strikes[i], gex_net[i]) for i in range(len(strikes)) if gex_net[i] < 0]
        neg_gex.sort(key=lambda x: x[1])
        pw_strikes = [int(x[0]) for x in neg_gex[:20]]
    
    while len(pw_strikes) < 20:
        pw_strikes.append(0)
    
    for i in range(20):
        nome = f"PW{i+1}" if i > 0 else "PW1_LP"
        metrics[nome] = pw_strikes[i] if i < len(pw_strikes) else 0
    
    # ========== 4. Pontos de Interesse ==========
    points = []
    if len(gex_net) > 0 and len(strikes) > 0:
        gex_abs = [(strikes[i], abs(gex_net[i])) for i in range(len(strikes))]
        gex_abs.sort(key=lambda x: x[1], reverse=True)
        
        for s, _ in gex_abs:
            if s not in points:
                points.append(int(s))
            if len(points) >= 20:
                break
    
    while len(points) < 20:
        points.append(0)
    
    for i in range(1, 21):
        metrics[f"Point_I{i}"] = points[i-1] if i-1 < len(points) else 0
    
    # ========== 5. Gamma Flip ==========
    gamma_flip = 0
    if len(gex_net) > 0 and len(strikes) > 0:
        for i in range(1, len(gex_net)):
            if gex_net[i-1] * gex_net[i] <= 0:
                s1, s2 = strikes[i-1], strikes[i]
                g1, g2 = gex_net[i-1], gex_net[i]
                if abs(g2 - g1) > 1e-12:
                    gamma_flip = int(round(s1 - g1 * (s2 - s1) / (g2 - g1)))
                else:
                    gamma_flip = int(round((s1 + s2) / 2))
                break
    
    metrics["GamaFlip_A"] = gamma_flip if gamma_flip is not None else 0
    metrics["GamaFlip_B"] = 0
    metrics["GamaFlip_C"] = 0
    
    # ========== 6. Vol Trigger ==========
    vol_trigger = 0
    if len(gex_net) > 0 and len(strikes) > 0:
        try:
            max_gex_idx = np.argmax(gex_net)
            min_gex_idx = np.argmin(gex_net)
            gamma_wall = strikes[max_gex_idx]
            gamma_risk = strikes[min_gex_idx]
            vol_trigger = int(round(gamma_wall - 0.75 * (gamma_wall - gamma_risk)))
        except (ValueError, IndexError):
            vol_trigger = 0
    
    metrics["Vol_TriggerA"] = vol_trigger if vol_trigger is not None else 0
    metrics["Vol_TriggerB"] = 0
    metrics["Vol_TriggerC"] = 0
    metrics["Vol_TriggerD"] = 0
    
    # ========== 7. Max/Min por expiração ==========
    metrics["Max_CW_0DTE"] = 0
    metrics["Min_PW_0DTE"] = 0
    metrics["Max_CW_MONTH"] = 0
    metrics["Min_PW_MONTH"] = 0
    metrics["Max_CW_ALL"] = 0
    metrics["Min_PW_ALL"] = 0
    
    if df is not None and not df.empty and 'ExpirationDate' in df.columns:
        try:
            today = pd.Timestamp.now().normalize().date()
            
            # 0DTE
            df_0dte = df[df['ExpirationDate'].dt.date == today]
            if not df_0dte.empty:
                df_0dte['GEX'] = df_0dte['Gamma'] * df_0dte['Open Interest'] * 100 * spot * spot * 0.01
                gex_0dte = df_0dte.groupby('Strike')['GEX'].sum()
                if not gex_0dte.empty:
                    metrics["Max_CW_0DTE"] = int(round(gex_0dte.idxmax())) if not pd.isna(gex_0dte.idxmax()) else 0
                    metrics["Min_PW_0DTE"] = int(round(gex_0dte.idxmin())) if not pd.isna(gex_0dte.idxmin()) else 0
            
            # MONTH
            is_third_friday = (df['ExpirationDate'].dt.weekday == 4) & (df['ExpirationDate'].dt.day.between(15, 21))
            df_month = df[is_third_friday]
            if not df_month.empty:
                df_month['GEX'] = df_month['Gamma'] * df_month['Open Interest'] * 100 * spot * spot * 0.01
                gex_month = df_month.groupby('Strike')['GEX'].sum()
                if not gex_month.empty:
                    metrics["Max_CW_MONTH"] = int(round(gex_month.idxmax())) if not pd.isna(gex_month.idxmax()) else 0
                    metrics["Min_PW_MONTH"] = int(round(gex_month.idxmin())) if not pd.isna(gex_month.idxmin()) else 0
            
            # ALL
            df['GEX'] = df['Gamma'] * df['Open Interest'] * 100 * spot * spot * 0.01
            gex_all = df.groupby('Strike')['GEX'].sum()
            if not gex_all.empty:
                metrics["Max_CW_ALL"] = int(round(gex_all.idxmax())) if not pd.isna(gex_all.idxmax()) else 0
                metrics["Min_PW_ALL"] = int(round(gex_all.idxmin())) if not pd.isna(gex_all.idxmin()) else 0
        except Exception:
            pass
    
    # ========== 8. MAX_PAIN ==========
    max_pain = 0
    if df is not None and not df.empty and len(strikes) > 0:
        try:
            pain_dict = {}
            for strike in strikes:
                call_oi = df[(df['Strike'] == strike) & (df['Type'] == 'Call')]['Open Interest'].sum()
                put_oi = df[(df['Strike'] == strike) & (df['Type'] == 'Put')]['Open Interest'].sum()
                pain = call_oi * max(0, spot - strike) + put_oi * max(0, strike - spot)
                pain_dict[strike] = pain
            
            if pain_dict:
                max_pain = max(pain_dict, key=pain_dict.get) if pain_dict else spot
        except Exception:
            max_pain = 0
    
    metrics["MAX_PAIN"] = int(round(max_pain)) if max_pain is not None else 0
    
    # ========== 9. NET_VANNA ==========
    net_vanna = 0
    if len(strikes) > 0:
        try:
            vanna_call = pivots["VANNA"]["Call"].values
            vanna_put = pivots["VANNA"]["Put"].values
            vanna_net = vanna_call - vanna_put
            
            if len(vanna_net) > 0:
                max_vanna_idx = np.argmax(np.abs(vanna_net))
                net_vanna = int(strikes[max_vanna_idx]) if max_vanna_idx < len(strikes) else 0
        except (KeyError, AttributeError, TypeError, IndexError):
            net_vanna = 0
    
    metrics["NET_VANNA"] = net_vanna if net_vanna is not None else 0
    
    # ========== 10. BN_1 a BN_12 ==========
    for i in range(1, 13):
        metrics[f"BN_{i}"] = 0
    
    # ========== 11. Métricas Delta ==========
    # Inicializar com valores padrão
    metrics["Delta_S1"] = 0
    metrics["Delta_S2"] = 0
    metrics["Delta_S3"] = 0
    metrics["Delta_R1"] = 0
    metrics["Delta_R2"] = 0
    metrics["Delta_R3"] = 0
    metrics["Delta_Flip"] = 0
    metrics["Delta_T_UP"] = 0
    metrics["Delta_T_DOWN"] = 0
    metrics["Delta_Max_Buy"] = 0
    metrics["Delta_Max_Sell"] = 0
    metrics["GVC_Strike"] = 0
    metrics["DNB_Low"] = 0
    metrics["DNB_High"] = 0
    metrics["Delta_NZ"] = 0.0
    metrics["GFS"] = 0.0
    metrics["PCOR"] = 1.0
    metrics["Delta_AC1_Buy"] = 0
    metrics["Delta_AC2_Buy"] = 0
    metrics["Delta_AC1_Sell"] = 0
    metrics["Delta_AC2_Sell"] = 0
    
    if len(strikes) > 0 and pivots is not None:
        try:
            dex_call = pivots["DEX"]["Call"].values
            dex_put = pivots["DEX"]["Put"].values
            dex_net = dex_call + dex_put
            
            if len(dex_net) > 0 and len(strikes) > 0:
                # Suportes
                suportes = []
                for i, s in enumerate(strikes):
                    if i < len(dex_net) and s < spot and dex_net[i] < 0:
                        suportes.append((s, abs(dex_net[i])))
                suportes.sort(key=lambda x: x[1], reverse=True)
                suportes = [int(s[0]) for s in suportes[:3]]
                while len(suportes) < 3:
                    suportes.append(0)
                
                metrics["Delta_S1"] = suportes[0]
                metrics["Delta_S2"] = suportes[1]
                metrics["Delta_S3"] = suportes[2]
                
                # Resistências
                resistencias = []
                for i, s in enumerate(strikes):
                    if i < len(dex_net) and s > spot and dex_net[i] > 0:
                        resistencias.append((s, dex_net[i]))
                resistencias.sort(key=lambda x: x[1], reverse=True)
                resistencias = [int(s[0]) for s in resistencias[:3]]
                while len(resistencias) < 3:
                    resistencias.append(0)
                
                metrics["Delta_R1"] = resistencias[0]
                metrics["Delta_R2"] = resistencias[1]
                metrics["Delta_R3"] = resistencias[2]
                
                # Delta Flip
                cum_delta = np.cumsum(dex_net)
                delta_flip = 0
                for i in range(1, len(cum_delta)):
                    if cum_delta[i-1] * cum_delta[i] <= 0:
                        s1, s2 = strikes[i-1], strikes[i]
                        d1, d2 = cum_delta[i-1], cum_delta[i]
                        if d2 != d1:
                            delta_flip = s1 - d1 * (s2 - s1) / (d2 - d1)
                        else:
                            delta_flip = (s1 + s2) / 2
                        break
                metrics["Delta_Flip"] = int(round(delta_flip)) if delta_flip > 0 else 0
                
                # Delta Max Buy / Sell
                if len(dex_net) > 0:
                    max_buy_idx = np.argmax(dex_net)
                    max_sell_idx = np.argmin(dex_net)
                    metrics["Delta_Max_Buy"] = int(strikes[max_buy_idx]) if max_buy_idx < len(strikes) else 0
                    metrics["Delta_Max_Sell"] = int(strikes[max_sell_idx]) if max_sell_idx < len(strikes) else 0
                
                # DNB
                max_delta_abs = np.max(np.abs(dex_net)) if len(dex_net) > 0 else 1
                neutros = []
                for i, d in enumerate(dex_net):
                    if i < len(strikes) and abs(d) <= 0.2 * max_delta_abs:
                        neutros.append(strikes[i])
                
                if neutros:
                    dnb_low = min(neutros)
                    dnb_high = max(neutros)
                else:
                    dnb_low = int(spot * 0.98) if spot > 0 else 0
                    dnb_high = int(spot * 1.02) if spot > 0 else 0
                
                metrics["DNB_Low"] = int(dnb_low)
                metrics["DNB_High"] = int(dnb_high)
                metrics["Delta_NZ"] = (dnb_low + dnb_high) / 2
                
                # GVC_Strike
                if df is not None and not df.empty:
                    if 'Volume' in df.columns and 'Open Interest' in df.columns:
                        df['Importance'] = df['Volume'] + df['Open Interest']
                        importance_agg = df.groupby('Strike')['Importance'].sum()
                        if not importance_agg.empty:
                            gvc = importance_agg.idxmax()
                            metrics["GVC_Strike"] = int(round(gvc)) if not pd.isna(gvc) else 0
                
                # PCOR
                if df is not None and not df.empty:
                    total_call_oi = df[df['Type'] == 'Call']['Open Interest'].sum()
                    total_put_oi = df[df['Type'] == 'Put']['Open Interest'].sum()
                    metrics["PCOR"] = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
                
                # Delta T_UP / T_DOWN
                metrics["Delta_T_UP"] = int(round(spot * 1.02)) if spot > 0 else 0
                metrics["Delta_T_DOWN"] = int(round(spot * 0.98)) if spot > 0 else 0
        except Exception:
            pass
    
    # ========== 12. COMPRA e VENDA ==========
    for i in range(1, 5):
        metrics[f"COMPRA{i}"] = 0
        metrics[f"VENDA{i}"] = 0
    
    # ========== 13. Action Points ==========
    metrics["Vol_Attack"] = 0
    metrics["A_Zero"] = 0
    
    for i in range(1, 11):
        metrics[f"ACT_P{i}_CW"] = 0
        metrics[f"ACT_P{i}_PW"] = 0
    
    return metrics

def calcular_metricas_a2(strikes, pivots, spot, basis, converter=False):
    """
    Calcula todas as métricas do relatório A2 a partir dos pivots.
    
    Baseado no código do WTS_GPHM.py: _calcular_metricas_dos_pivots()
    
    Args:
        strikes (list): Lista de strikes
        pivots (dict): Dicionário com os pivots de cada métrica
        spot (float): Preço spot
        basis (float): Basis para conversão
        converter (bool): Se True, converte os strikes para CVS
    
    Returns:
        dict: Dicionário com todas as métricas calculadas
    """
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame(index=strikes)
    df.index.name = 'Strike'
    
    for metric in ['Open Interest', 'Volume', 'DEX', 'GEX', 'VANNA']:
        df[f'{metric}_Call'] = pivots[metric]['Call'].values
        df[f'{metric}_Put'] = pivots[metric]['Put'].values
    
    df['Net_GEX'] = df['GEX_Call'] - df['GEX_Put']
    df['Net_VANNA'] = df['VANNA_Call'] - df['VANNA_Put']
    df['Net_Delta_MM'] = - (df['DEX_Call'] - df['DEX_Put'])
    
    # Aplica conversão dos strikes se necessário
    if converter and basis > 0 and spot > 0:
        fator = basis / spot
        df.index = df.index * fator
        spot_ref = basis  # spot convertido = basis
    else:
        spot_ref = spot
    
    df.sort_index(inplace=True)
    metrics = {}
    
    # ========== 1. CALL WALL OI ==========
    if not df.empty:
        idx_max_call_oi = df['Open Interest_Call'].idxmax()
        metrics['CALL_WALL_OI'] = idx_max_call_oi if not pd.isna(idx_max_call_oi) else 0
    else:
        metrics['CALL_WALL_OI'] = 0
    
    # ========== 2. PUT WALL OI ==========
    if not df.empty:
        idx_max_put_oi = df['Open Interest_Put'].idxmax()
        metrics['PUT_WALL_OI'] = idx_max_put_oi if not pd.isna(idx_max_put_oi) else 0
    else:
        metrics['PUT_WALL_OI'] = 0
    
    # ========== 3. CALL WALL VOL ==========
    if not df.empty:
        idx_max_call_vol = df['Volume_Call'].idxmax()
        metrics['CALL_WALL_VOL'] = idx_max_call_vol if not pd.isna(idx_max_call_vol) else 0
    else:
        metrics['CALL_WALL_VOL'] = 0
    
    # ========== 4. PUT WALL VOL ==========
    if not df.empty:
        idx_max_put_vol = df['Volume_Put'].idxmax()
        metrics['PUT_WALL_VOL'] = idx_max_put_vol if not pd.isna(idx_max_put_vol) else 0
    else:
        metrics['PUT_WALL_VOL'] = 0
    
    # ========== 5. GAMMA WALL / GAMMA RISK ==========
    if not df.empty:
        idx_max_gamma = df['Net_GEX'].idxmax()
        idx_min_gamma = df['Net_GEX'].idxmin()
        metrics['GAMMA_WALL'] = idx_max_gamma if not pd.isna(idx_max_gamma) else 0
        metrics['GAMMA_RISK'] = idx_min_gamma if not pd.isna(idx_min_gamma) else 0
    else:
        metrics['GAMMA_WALL'] = 0
        metrics['GAMMA_RISK'] = 0
    
    # ========== 6. GAMMA FLIP (interpolação contínua) ==========
    if len(df) > 1:
        net_gex = df['Net_GEX'].values
        strikes_arr = df.index.values
        zero_cross_idx = None
        for i in range(len(net_gex)-1):
            if net_gex[i] * net_gex[i+1] <= 0:
                zero_cross_idx = i
                break
        if zero_cross_idx is not None:
            s1, s2 = strikes_arr[zero_cross_idx], strikes_arr[zero_cross_idx+1]
            g1, g2 = net_gex[zero_cross_idx], net_gex[zero_cross_idx+1]
            if g2 != g1:
                metrics['GAMMA_FLIP'] = s1 + (0 - g1) * (s2 - s1) / (g2 - g1)
            else:
                metrics['GAMMA_FLIP'] = (s1 + s2) / 2
        else:
            idx_min_abs = np.argmin(np.abs(net_gex))
            metrics['GAMMA_FLIP'] = strikes_arr[idx_min_abs]
    else:
        metrics['GAMMA_FLIP'] = 0
    
    # ========== 7. VOL_TRIGGER ==========
    if metrics['GAMMA_WALL'] != 0 and metrics['GAMMA_RISK'] != 0:
        metrics['VOL_TRIGGER'] = metrics['GAMMA_WALL'] - 0.75 * (metrics['GAMMA_WALL'] - metrics['GAMMA_RISK'])
    else:
        metrics['VOL_TRIGGER'] = 0
    
    # ========== 8. VANNA ==========
    if 'Net_VANNA' in df.columns and not df['Net_VANNA'].isna().all():
        neg_vanna = df[df['Net_VANNA'] < 0]
        if not neg_vanna.empty:
            idx_min_vanna = neg_vanna['Net_VANNA'].idxmin()
            metrics['VANNA_MM_COMPRA_FUTUROS'] = idx_min_vanna if not pd.isna(idx_min_vanna) else 0
        else:
            metrics['VANNA_MM_COMPRA_FUTUROS'] = 0
        
        pos_vanna = df[df['Net_VANNA'] > 0]
        if not pos_vanna.empty:
            idx_max_vanna = pos_vanna['Net_VANNA'].idxmax()
            metrics['VANNA_MM_VENDE_FUTUROS'] = idx_max_vanna if not pd.isna(idx_max_vanna) else 0
        else:
            metrics['VANNA_MM_VENDE_FUTUROS'] = 0
        
        metrics['VANNA_IV_ACELERA_QUEDA'] = metrics['VANNA_MM_COMPRA_FUTUROS']
        metrics['VANNA_IV_ACELERA_ALTA'] = metrics['VANNA_MM_VENDE_FUTUROS']
    else:
        metrics['VANNA_MM_COMPRA_FUTUROS'] = 0
        metrics['VANNA_MM_VENDE_FUTUROS'] = 0
        metrics['VANNA_IV_ACELERA_QUEDA'] = 0
        metrics['VANNA_IV_ACELERA_ALTA'] = 0
    
    # ========== 9. FLUXO DEFESA TOPO ==========
    acima = df[df.index > spot_ref].nlargest(3, 'Open Interest_Put')
    metrics['FLUXO_DEFESA_TOPO'] = acima.index.tolist() if not acima.empty else []
    
    # ========== 10. FLUXO DEFESA FUNDO ==========
    abaixo = df[df.index < spot_ref].nlargest(3, 'Open Interest_Call')
    metrics['FLUXO_DEFESA_FUNDO'] = abaixo.index.tolist() if not abaixo.empty else []
    
    # ========== 11. AMPLIFICA ACIMA ==========
    gamma_acima = df[(df.index > spot_ref) & (df['Net_GEX'] < 0)].nsmallest(3, 'Net_GEX')
    metrics['AMPLIFICA_ACIMA'] = gamma_acima.index.tolist() if not gamma_acima.empty else []
    
    # ========== 12. AMPLIFICA ABAIXO ==========
    gamma_abaixo = df[(df.index < spot_ref) & (df['Net_GEX'] < 0)].nsmallest(3, 'Net_GEX')
    metrics['AMPLIFICA_ABAIXO'] = gamma_abaixo.index.tolist() if not gamma_abaixo.empty else []
    
    # ========== 13. PRESSAO MM COMPRADOR ==========
    mm_compra = df[df['Net_Delta_MM'] < 0].nsmallest(3, 'Net_Delta_MM')
    metrics['PRESSAO_MM_COMPRADOR'] = mm_compra.index.tolist() if not mm_compra.empty else []
    
    # ========== 14. PRESSAO MM VENDEDOR ==========
    mm_vende = df[df['Net_Delta_MM'] > 0].nlargest(3, 'Net_Delta_MM')
    metrics['PRESSAO_MM_VENDEDOR'] = mm_vende.index.tolist() if not mm_vende.empty else []
    
    # ========== 15. WAR ZONE ==========
    if len(df) > 0:
        gamma_abs = df['Net_GEX'].abs()
        delta_abs = df['Net_Delta_MM'].abs()
        gamma_thresh = gamma_abs.quantile(0.8) if len(gamma_abs) > 0 else 0
        delta_thresh = delta_abs.quantile(0.7) if len(delta_abs) > 0 else 0
        war = df[(gamma_abs > gamma_thresh) & (delta_abs > delta_thresh)].nlargest(3, 'Net_GEX')
        metrics['WAR_ZONE'] = war.index.tolist() if not war.empty else []
    else:
        metrics['WAR_ZONE'] = []
    
    # ========== 16. DEX CENTRO MAGNETICO ==========
    if len(df) > 1:
        net_delta = df['Net_Delta_MM'].values
        strikes_arr = df.index.values
        zero_cross_idx = None
        for i in range(len(net_delta)-1):
            if net_delta[i] * net_delta[i+1] <= 0:
                zero_cross_idx = i
                break
        if zero_cross_idx is not None:
            s1, s2 = strikes_arr[zero_cross_idx], strikes_arr[zero_cross_idx+1]
            d1, d2 = net_delta[zero_cross_idx], net_delta[zero_cross_idx+1]
            if d2 != d1:
                metrics['DEX_CENTRO_MAGNETICO'] = s1 + (0 - d1) * (s2 - s1) / (d2 - d1)
            else:
                metrics['DEX_CENTRO_MAGNETICO'] = (s1 + s2) / 2
        else:
            idx_min_abs = np.argmin(np.abs(net_delta))
            metrics['DEX_CENTRO_MAGNETICO'] = strikes_arr[idx_min_abs]
    else:
        metrics['DEX_CENTRO_MAGNETICO'] = 0
    
    # ========== 17. DEX ZONA NEUTRA ==========
    max_delta_abs = df['Net_Delta_MM'].abs().max()
    if max_delta_abs > 0:
        neutros = df[df['Net_Delta_MM'].abs() <= 0.2 * max_delta_abs]
        if not neutros.empty:
            metrics['DEX_ZONA_NEUTRA'] = (neutros.index.min(), neutros.index.max())
        else:
            metrics['DEX_ZONA_NEUTRA'] = (spot_ref - 0.5, spot_ref + 0.5)
    else:
        metrics['DEX_ZONA_NEUTRA'] = (spot_ref - 0.5, spot_ref + 0.5)
    
    # ========== 18. DEX HEDGE QUEDA / ALTA ==========
    if not df.empty:
        idx_min_delta = df['Net_Delta_MM'].idxmin()
        idx_max_delta = df['Net_Delta_MM'].idxmax()
        metrics['DEX_HEDGE_QUEDA'] = idx_min_delta if not pd.isna(idx_min_delta) else 0
        metrics['DEX_HEDGE_ALTA'] = idx_max_delta if not pd.isna(idx_max_delta) else 0
    else:
        metrics['DEX_HEDGE_QUEDA'] = 0
        metrics['DEX_HEDGE_ALTA'] = 0
    
    # ========== 19. ALVOS ==========
    strikes_sorted = df.index.tolist()
    if strikes_sorted:
        above = [s for s in strikes_sorted if s > spot_ref]
        below = [s for s in strikes_sorted if s < spot_ref]
        metrics['ALVO_SUPERIOR'] = above[0] if above else 0
        metrics['ALVO_INFERIOR'] = below[-1] if below else 0
    else:
        metrics['ALVO_SUPERIOR'] = 0
        metrics['ALVO_INFERIOR'] = 0
    
    return metrics

def formatar_metricas_a2(metrics):
    """
    Formata as métricas do A2 conforme especificação.
    
    Baseado no código do WTS_GPHM.py: _formatar_metricas()
    
    Args:
        metrics (dict): Dicionário com as métricas calculadas
    
    Returns:
        list: Lista de strings formatadas
    """
    import pandas as pd
    import numpy as np
    
    linhas = []
    
    ordem = [
        'CALL_WALL_OI',
        'PUT_WALL_OI',
        'CALL_WALL_VOL',
        'PUT_WALL_VOL',
        'GAMMA_WALL',
        'GAMMA_RISK',
        'GAMMA_FLIP',
        'VOL_TRIGGER',
        'VANNA_MM_COMPRA_FUTUROS',
        'VANNA_MM_VENDE_FUTUROS',
        'VANNA_IV_ACELERA_QUEDA',
        'VANNA_IV_ACELERA_ALTA',
        'FLUXO_DEFESA_TOPO',
        'FLUXO_DEFESA_FUNDO',
        'AMPLIFICA_ACIMA',
        'AMPLIFICA_ABAIXO',
        'PRESSAO_MM_COMPRADOR',
        'PRESSAO_MM_VENDEDOR',
        'WAR_ZONE',
        'DEX_CENTRO_MAGNETICO',
        'DEX_ZONA_NEUTRA',
        'DEX_HEDGE_QUEDA',
        'DEX_HEDGE_ALTA',
        'ALVO_SUPERIOR',
        'ALVO_INFERIOR'
    ]
    
    campos_lista = {
        'FLUXO_DEFESA_TOPO', 'FLUXO_DEFESA_FUNDO',
        'AMPLIFICA_ACIMA', 'AMPLIFICA_ABAIXO',
        'PRESSAO_MM_COMPRADOR', 'PRESSAO_MM_VENDEDOR',
        'WAR_ZONE'
    }
    
    for key in ordem:
        val = metrics.get(key, np.nan)
        
        # --- Listas (desmembrar) ---
        if key in campos_lista:
            if isinstance(val, list) and val:
                for i, item in enumerate(val, start=1):
                    if isinstance(item, (int, float)):
                        if item == int(item):
                            item_str = f"{int(item)}"
                        else:
                            item_str = f"{item:.2f}"
                    else:
                        item_str = str(item)
                    linhas.append(f"{key}{i}({item_str});")
            # Lista vazia: não gera linha
            continue
        
        # --- DEX_ZONA_NEUTRA como dois campos individuais ---
        if key == 'DEX_ZONA_NEUTRA':
            if isinstance(val, tuple) and len(val) == 2:
                min_val, max_val = val
                min_str = f"{int(min_val)}" if min_val == int(min_val) else f"{min_val:.2f}"
                max_str = f"{int(max_val)}" if max_val == int(max_val) else f"{max_val:.2f}"
                linhas.append(f"{key}1({min_str});")
                linhas.append(f"{key}2({max_str});")
            else:
                linhas.append(f"{key}1(0000);")
                linhas.append(f"{key}2(0000);")
            continue
        
        # --- Campos numéricos simples ---
        if pd.isna(val):
            linhas.append(f"{key}(0000);")
        else:
            if val == int(val):
                linhas.append(f"{key}({int(val)});")
            else:
                linhas.append(f"{key}({val:.2f});")
    
    return linhas

def gerar_relatorio_a2_streamlit(df, spot, basis, symbol, active_expiry_filter, strikes, pivots):
    """
    Gera o relatório A2 no Streamlit seguindo o padrão do WTS_GPHM.py
    
    Baseado no código do WTS_GPHM.py: exportar_analise_a2()
    
    Args:
        df (DataFrame): DataFrame filtrado
        spot (float): Preço spot
        basis (float): Basis de conversão
        symbol (str): Símbolo do ativo
        active_expiry_filter (str): Filtro de vencimento ativo
        strikes (list): Lista de strikes
        pivots (dict): Dicionário com os pivots
    
    Returns:
        tuple: (texto_do_relatorio, nome_do_arquivo)
    """
    import re
    from datetime import datetime
    
    # ========== 1. VALIDAÇÕES ==========
    if abs(basis - 1.0) < 1e-6:
        return "⚠️ BASIS OF CONVERSION deve ser diferente de 1 para gerar o relatório.", None
    
    if df is None or df.empty:
        return f"⚠️ Nenhum dado encontrado para o filtro: {active_expiry_filter}", None
    
    if not strikes or not pivots:
        return "⚠️ Dados de strikes ou pivots insuficientes para gerar o relatório.", None
    
    # ========== 2. MODO DE EXPIRAÇÃO ==========
    modo_texto = active_expiry_filter if active_expiry_filter else "TODOS (Todos os vencimentos)"
    
    # ========== 3. DATA ==========
    data_str = datetime.now().strftime('%d/%m/%Y')
    
    # ========== 4. CALCULAR MÉTRICAS ==========
    metricas_originais = calcular_metricas_a2(strikes, pivots, spot, basis, converter=False)
    metricas_convertidas = calcular_metricas_a2(strikes, pivots, spot, basis, converter=True)
    
    # ========== 5. FORMATAR RELATÓRIO ==========
    linhas = []
    
    # Seção Original
    linhas.append(f"ANALISE REALIZADA: EM {data_str}")
    linhas.append("")
    linhas.append(f"MODO DE EXPIRAÇÃO: {modo_texto}")
    linhas.append("")
    linhas.append(f"BASIS_OF_CONVERSION_D1\t({basis:.2f});")
    linhas.append(f"CLOSE_SPOT_D1\t({spot:.2f});")
    linhas.append("")
    linhas.extend(formatar_metricas_a2(metricas_originais))
    
    # Seção Convertida
    linhas.append("")
    linhas.append("")
    linhas.append(f"ANALISE CONVERTIDA: EM {data_str}")
    linhas.append("")
    linhas.append(f"BASIS_OF_CONVERSION_D1\t({basis:.2f});")
    linhas.append(f"CLOSE_SPOT_D1\t({spot:.2f});")
    linhas.append("")
    linhas.extend(formatar_metricas_a2(metricas_convertidas))
    
    # Rodapé
    ratio = basis / spot if spot != 0 else 1.0
    linhas.append("")
    linhas.append("")
    linhas.append(f"✅ CONVERSÃO APLICADA: ratio = {ratio:.4f} (winfut/asset)")
    linhas.append(f"✅ SPOT USADO: {spot:.2f} (AUTOMÁTICO)")
    linhas.append(f"✅ BASIS USADO: {basis:.2f}")
    
    texto = "\n".join(linhas)
    
    # ========== 6. GERAR NOME DO ARQUIVO ==========
    data_hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
    simbolo_limpo = re.sub(r'[^\w]', '_', symbol).upper()
    
    filtro_abrev = {
        "ALL Expiry": "ALL",
        "MONTH Expiry": "MONTH",
        "0DTE + 4 Expiry": "0DTE_PLUS_4",
        "0DTE Expiry": "0DTE",
        "0DTE +1 Plus Friday": "0DTE_FRI",
        "0DTE Expiry +1": "0DTE_PLUS1",
        None: "ALL"
    }.get(active_expiry_filter, "ALL")
    
    nome_arquivo = f"WTS_GP_{data_hoje}_{simbolo_limpo}_{filtro_abrev}_A2.txt"
    
    return texto, nome_arquivo

def gerar_relatorio_a3_streamlit(df, spot, basis, symbol, active_expiry_filter, strikes, pivots):
    """
    🆕 Gera o relatório A3 com strikes das LINHAS plotadas no gráfico.
    
    Lê diretamente de:
    - st.session_state["lines_pcp"] → Strikes Principais (Pcp)
    - st.session_state["lines_int"] → Strikes Intermediários (Int)
    
    Returns:
        tuple: (texto_do_relatorio, nome_do_arquivo)
    """
    import re
    from datetime import datetime

    # ========== 1. VALIDAÇÕES ==========
    if abs(basis - 1.0) < 1e-6:
        return "⚠️ BASIS OF CONVERSION deve ser diferente de 1 para gerar o relatório.", None

    if df is None or df.empty:
        return f"⚠️ Nenhum dado encontrado para o filtro: {active_expiry_filter}", None

    # ========== 2. 🆕 LER DAS LINHAS PLOTADAS ==========
    pcp_list = st.session_state.get("lines_pcp", [])
    int_list = st.session_state.get("lines_int", [])

    if not pcp_list and not int_list:
        return "⚠️ Nenhuma linha adicionada no gráfico. Use a aba 'Gamma Points' para adicionar linhas Pcp e Int.", None

    # ========== 3. PREPARAR LISTAS DE 10 (COMPLETAR COM 0) ==========
    pcp_orig = list(pcp_list)  # Cópia
    int_orig = list(int_list)  # Cópia

    while len(pcp_orig) < 10:
        pcp_orig.append(0)
    while len(int_orig) < 10:
        int_orig.append(0)

    # Trunca em 10 se tiver mais
    pcp_orig = pcp_orig[:10]
    int_orig = int_orig[:10]

    # ========== 4. CONVERTER PARA CVS ==========
    pcp_cvs = []
    for s in pcp_orig:
        if s == 0:
            pcp_cvs.append(0)
        else:
            pcp_cvs.append(calcular_cvs(s, basis, spot))

    int_cvs = []
    for s in int_orig:
        if s == 0:
            int_cvs.append(0)
        else:
            int_cvs.append(calcular_cvs(s, basis, spot))

    # ========== 5. MODO DE EXPIRAÇÃO ==========
    modo_texto = active_expiry_filter if active_expiry_filter else "TODOS (Todos os vencimentos)"

    # ========== 6. DATA ==========
    data_str = datetime.now().strftime('%d/%m/%Y')

    # ========== 7. MONTAR RELATÓRIO ==========
    linhas = []

    # Seção Original
    linhas.append(f"ANALISE REALIZADA: EM {data_str}")
    linhas.append("")
    linhas.append(f"MODO DE EXPIRAÇÃO: {modo_texto}")
    linhas.append("")
    linhas.append(f"BASIS_OF_CONVERSION_D1\t({basis:.2f});")
    linhas.append(f"CLOSE_SPOT_D1\t({spot:.2f});")
    linhas.append("")

    for i, s in enumerate(pcp_orig, 1):
        val_str = f"{int(s)}" if s != 0 else "0000"
        linhas.append(f"AN_Pcp_P{i}\t({val_str});")

    for i, s in enumerate(int_orig, 1):
        val_str = f"{int(s)}" if s != 0 else "0000"
        linhas.append(f"AN_Int_P{i}\t({val_str});")

    # Seção Convertida
    linhas.append("")
    linhas.append("")
    linhas.append(f"ANALISE CONVERTIDA: EM {data_str}")
    linhas.append("")
    linhas.append(f"BASIS_OF_CONVERSION_D1\t({basis:.2f});")
    linhas.append(f"CLOSE_SPOT_D1\t({spot:.2f});")
    linhas.append("")

    for i, cvs in enumerate(pcp_cvs, 1):
        val_str = f"{int(cvs)}" if cvs != 0 else "0000"
        linhas.append(f"AN_Pcp_P{i}\t({val_str});")

    for i, cvs in enumerate(int_cvs, 1):
        val_str = f"{int(cvs)}" if cvs != 0 else "0000"
        linhas.append(f"AN_Int_P{i}\t({val_str});")

    # Rodapé
    ratio = basis / spot if spot != 0 else 1.0
    linhas.append("")
    linhas.append("")
    linhas.append(f"✅ CONVERSÃO APLICADA: ratio = {ratio:.4f} (winfut/asset)")
    linhas.append(f"✅ SPOT USADO: {spot:.2f} (AUTOMÁTICO)")
    linhas.append(f"✅ BASIS USADO: {basis:.2f}")
    linhas.append(f"✅ STRIKES PCP: {len([s for s in pcp_orig if s != 0])}")
    linhas.append(f"✅ STRIKES INT: {len([s for s in int_orig if s != 0])}")

    texto = "\n".join(linhas)

    # ========== 8. GERAR NOME DO ARQUIVO ==========
    data_hoje = datetime.now().strftime("%Y%m%d_%H%M%S")
    simbolo_limpo = re.sub(r'[^\w]', '_', symbol).upper()

    filtro_abrev = {
        "ALL Expiry": "ALL",
        "MONTH Expiry": "MONTH",
        "0DTE + 4 Expiry": "0DTE_PLUS_4",
        "0DTE Expiry": "0DTE",
        "0DTE +1 Plus Friday": "0DTE_FRI",
        "0DTE Expiry +1": "0DTE_PLUS1",
        None: "ALL"
    }.get(active_expiry_filter, "ALL")

    nome_arquivo = f"WTS_GP_{data_hoje}_{simbolo_limpo}_{filtro_abrev}_A3.txt"

    return texto, nome_arquivo


def baixar_relatorio_a1_streamlit(df, spot, basis, symbol, active_expiry_filter, strikes, pivots):
    """
    Gera o relatório A1 e retorna para download no Streamlit
    
    Returns:
        tuple: (texto_do_relatorio, nome_do_arquivo)
    """
    from datetime import datetime
    import re
    
    # Validar BASIS
    if abs(basis - 1.0) < 1e-6:
        return "⚠️ BASIS OF CONVERSION deve ser diferente de 1 para gerar o relatório.", None
    
    # Gerar o texto do relatório
    texto = gerar_relatorio_a1_streamlit(df, spot, basis, symbol, active_expiry_filter, strikes, pivots)
    
    # Gerar nome do arquivo
    data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    simbolo_limpo = re.sub(r'[^\w]', '_', symbol).upper()
    
    filtro_abrev = {
        "ALL Expiry": "ALL",
        "MONTH Expiry": "MONTH",
        "0DTE + 4 Expiry": "0DTE_PLUS_4",
        "0DTE Expiry": "0DTE",
        "0DTE +1 Plus Friday": "0DTE_FRI",
        "0DTE Expiry +1": "0DTE_PLUS1",
        None: "ALL"
    }.get(active_expiry_filter, "ALL")
    
    nome_arquivo = f"WTS_GP_{data_str}_{simbolo_limpo}_{filtro_abrev}_A1.txt"
    
    return texto, nome_arquivo
# =============================================================================
# FUNÇÃO FILTROS
# =============================================================================
def aplicar_filtro_vencimento(df, active_expiry_filter):
    """
    Aplica o filtro de vencimento ao DataFrame
    Baseado no código do WTS_GPHM.py
    """
    if df is None or df.empty:
        return df
    
    # Se for ALL Expiry, retorna o DataFrame original
    if active_expiry_filter is None or active_expiry_filter == "ALL Expiry":
        return df.copy()
    
    df_filtrado = df.copy()
    hoje = pd.Timestamp.now().normalize().date()
    
    # ========== FILTROS ESPECÍFICOS ==========
    if active_expiry_filter == "0DTE Expiry":
        # Vencimento do dia atual
        mask_today = df_filtrado['ExpirationDate'].dt.date == hoje
        if mask_today.any():
            return df_filtrado[mask_today].copy()
        # Fallback: vencimento mais próximo
        nearest_exp = df_filtrado['ExpirationDate'].dt.date.min()
        return df_filtrado[df_filtrado['ExpirationDate'].dt.date == nearest_exp].copy()
    
    elif active_expiry_filter == "MONTH Expiry":
        # Terceira sexta-feira do mês
        mask_monthly = (df_filtrado['ExpirationDate'].dt.weekday == 4) & \
                       (df_filtrado['ExpirationDate'].dt.day.between(15, 21))
        return df_filtrado[mask_monthly].copy()
    
    elif active_expiry_filter == "0DTE + 4 Expiry":
        # 0DTE + próximos 4 vencimentos
        unique_expiries = sorted(df_filtrado['ExpirationDate'].dt.date.unique())
        if not unique_expiries:
            return df_filtrado
        
        try:
            idx_0dte = unique_expiries.index(hoje)
        except ValueError:
            idx_0dte = 0
        
        selected_expiries = unique_expiries[idx_0dte:idx_0dte + 5]
        mask_selected = df_filtrado['ExpirationDate'].dt.date.isin(selected_expiries)
        return df_filtrado[mask_selected].copy()
    
    elif active_expiry_filter == "0DTE +1 Plus Friday":
        # 0DTE + próxima sexta-feira
        days_ahead = 4 - hoje.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_friday = hoje + pd.Timedelta(days=days_ahead)
        
        mask_0dte = df_filtrado['ExpirationDate'].dt.date == hoje
        mask_friday = df_filtrado['ExpirationDate'].dt.date == next_friday
        return df_filtrado[mask_0dte | mask_friday].copy()
    
    elif active_expiry_filter == "0DTE Expiry +1":
        # 0DTE + próximo vencimento
        unique_expiries = sorted(df_filtrado['ExpirationDate'].dt.date.unique())
        
        try:
            idx_0dte = unique_expiries.index(hoje)
            selected = unique_expiries[idx_0dte:idx_0dte + 2]
        except ValueError:
            selected = unique_expiries[:2]
        
        mask_selected = df_filtrado['ExpirationDate'].dt.date.isin(selected)
        return df_filtrado[mask_selected].copy()
    
    # Fallback
    return df_filtrado

def atualizar_dados_com_filtro():
    """
    Atualiza os dados aplicando o filtro de vencimento atual
    e recalcula os strikes e pivots
    """
    if not st.session_state["dados_carregados"]:
        return
    
    df = st.session_state["df_original"]
    spot = st.session_state["spot"]
    active_expiry_filter = st.session_state["active_expiry_filter"]
    
    # Aplicar filtro de vencimento
    df_filtrado = aplicar_filtro_vencimento(df, active_expiry_filter)
    st.session_state["df_filtrado"] = df_filtrado
    
    # Obter strikes únicos do DataFrame filtrado
    strikes_unicos = sorted(df_filtrado['Strike'].unique())
    st.session_state["strikes_unicos"] = strikes_unicos
    
    # Selecionar strikes com base na quantidade
    n_strikes = st.session_state.get("n_strikes", 40)
    step = st.session_state.get("step", 1)
    
    if strikes_unicos:
        idx_spot = min(range(len(strikes_unicos)), key=lambda i: abs(strikes_unicos[i] - spot))
        idx_min = max(0, idx_spot - n_strikes)
        idx_max = min(len(strikes_unicos) - 1, idx_spot + n_strikes)
        strikes_selecionados = strikes_unicos[idx_min:idx_max + 1:step]
        
        if not strikes_selecionados:
            strikes_selecionados = [strikes_unicos[idx_spot]]
    else:
        strikes_selecionados = []
    
    if strikes_selecionados:
        data_ref = datetime.now()
        strikes_calc, pivots = cache_calculo_exposicoes(df_filtrado, spot, tuple(strikes_selecionados))
        st.session_state["strikes_calc"] = strikes_calc
        st.session_state["pivots"] = pivots
    else:
        st.session_state["strikes_calc"] = []
        st.session_state["pivots"] = {}
    
    # ========== GERAR RELATÓRIOS AUTOMATICAMENTE ==========
    gerar_todos_relatorios()

def adicionar_linha_strike(strike, tipo='pcp'):
    """
    Adiciona uma linha visual no gráfico para um strike específico.
    
    Args:
        strike (float/int): Valor do strike
        tipo (str): 'pcp' (Principal) ou 'int' (Intermediário)
    
    Returns:
        bool: True se adicionado com sucesso
    """
    if strike is None:
        st.warning("⚠️ Strike inválido.")
        return False

    try:
        strike_int = int(round(float(strike)))
    except (TypeError, ValueError):
        st.warning(f"⚠️ Strike inválido: {strike}")
        return False

    # Inicializa listas se não existirem
    if "lines_pcp" not in st.session_state:
        st.session_state["lines_pcp"] = []
    if "lines_int" not in st.session_state:
        st.session_state["lines_int"] = []

    pcp_list = st.session_state["lines_pcp"]
    int_list = st.session_state["lines_int"]

    # ========== VALIDAÇÕES ==========
    if strike_int in pcp_list:
        st.warning(f"⚠️ Strike {strike_int} já possui linha Pcp!")
        return False

    if strike_int in int_list:
        st.warning(f"⚠️ Strike {strike_int} já possui linha Int!")
        return False

    if strike_int in pcp_list and tipo == 'int':
        st.warning(f"⚠️ Strike {strike_int} já é Pcp! Remova primeiro para mudar para Int.")
        return False

    if strike_int in int_list and tipo == 'pcp':
        st.warning(f"⚠️ Strike {strike_int} já é Int! Remova primeiro para mudar para Pcp.")
        return False

    # ========== ADICIONAR LINHA ==========
    if tipo == 'pcp':
        if len(pcp_list) >= 20:
            st.warning(f"⚠️ Limite de 20 linhas Pcp atingido!")
            return False
        st.session_state["lines_pcp"].append(strike_int)
        st.session_state["lines_pcp"].sort()  # Mantém ordenado
        st.success(f"✅ Linha Pcp adicionada no strike {strike_int}")
    else:
        if len(int_list) >= 20:
            st.warning(f"⚠️ Limite de 20 linhas Int atingido!")
            return False
        st.session_state["lines_int"].append(strike_int)
        st.session_state["lines_int"].sort()  # Mantém ordenado
        st.success(f"✅ Linha Int adicionada no strike {strike_int}")

    # ✅ Regenera relatórios (A3 agora lê das linhas)
    gerar_todos_relatorios()

    # ❌ REMOVIDO: st.rerun() - Não precisa forçar rerun
    return True


def remover_linha_strike(strike, tipo='pcp'):
    """
    Remove uma linha do gráfico.
    
    Args:
        strike (int): Valor do strike
        tipo (str): 'pcp' ou 'int'
    
    Returns:
        bool: True se removido com sucesso
    """
    try:
        strike_int = int(round(float(strike)))
    except (TypeError, ValueError):
        return False

    if tipo == 'pcp':
        if strike_int in st.session_state.get("lines_pcp", []):
            st.session_state["lines_pcp"].remove(strike_int)
            st.info(f"🗑️ Linha Pcp {strike_int} removida")
            gerar_todos_relatorios()
            # ❌ REMOVIDO: st.rerun()
            return True
    else:
        if strike_int in st.session_state.get("lines_int", []):
            st.session_state["lines_int"].remove(strike_int)
            st.info(f"🗑️ Linha Int {strike_int} removida")
            gerar_todos_relatorios()
            # ❌ REMOVIDO: st.rerun()
            return True

    return False


def limpar_todas_linhas():
    """Limpa todas as listas de linhas (Pcp e Int)"""
    st.session_state["lines_pcp"] = []
    st.session_state["lines_int"] = []
    gerar_todos_relatorios()
    st.success("🗑️ Todas as linhas foram removidas")

def exibir_abas_graficos():
    """Exibe as abas de gráficos com o filtro atual aplicado"""
    strikes_calc = st.session_state["strikes_calc"]
    pivots = st.session_state["pivots"]
    spot = st.session_state["spot"]
    basis = st.session_state["basis"]
    symbol = st.session_state["symbol"]
    active_expiry_filter = st.session_state["active_expiry_filter"]
    normalize = st.session_state["normalizacao_ativa"]
    strikes_unicos = st.session_state["strikes_unicos"]
    n_strikes = st.session_state["n_strikes"]
    step = st.session_state["step"]
    
    # ========== CRIAÇÃO DAS ABAS (11 ABAS) ==========
    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📊 Gamma Points",
        "📊 Total Gamma Exposure (Barras)",
        "📐 Gamma Exposure Profile (Curvas)",
        "📈 Todos os Gráficos",
        "📊 DEX (Delta Exposure)",
        "📈 GEX (Gamma Exposure)",
        "📊 VANNA",
        "📈 Volume",
        "📊 Open Interest",
        "📋 Dados Exportados",
        "📊 Relatórios"
    ])

    # ========== ABA 0: GAMMA POINTS (COM LINHAS DE STRIKES) ==========
    with tab0:
        st.subheader("📊 Gamma Points - Análise Completa")
        st.caption(f"Strikes exibidos: {len(strikes_calc)} (filtrado por {n_strikes} strikes cada lado, step={step})")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        st.caption("📌 DEX (branco) | Volume (cinza) | Open Interest (azul/vermelho) | VANNA (amarelo/fúcsia) | GEX (ciano) | GEPLS (curvas)")
        st.caption("📌 🟡 Linhas Pcp (amarelo sólida) | 🟡 Linhas Int (amarelo pontilhada)")
        
        # ========== CHECKBOXES (6 COLUNAS) ==========
        col_overlay1, col_overlay2, col_overlay3, col_overlay4, col_overlay5, col_overlay6 = st.columns(6)
        
        with col_overlay1:
            overlay_dex = st.checkbox("📊 DEX", value=True, key="overlay_dex_gp")
        with col_overlay2:
            overlay_volume = st.checkbox("📊 Volume", value=True, key="overlay_volume_gp")
        with col_overlay3:
            overlay_oi = st.checkbox("📊 Open Interest", value=True, key="overlay_oi_gp")
        with col_overlay4:
            overlay_vanna = st.checkbox("📊 VANNA", value=True, key="overlay_vanna_gp")
        with col_overlay5:
            overlay_gex = st.checkbox("📈 GEX", value=True, key="overlay_gex_gp")
        with col_overlay6:
            overlay_gepls = st.checkbox("📈 GEPLS", value=True, key="overlay_gepls_gp")
        
        # ========== OVERLAYS (BARRAS) ==========
        overlays = []
        if overlay_volume:
            overlays.append("Volume")
        if overlay_oi:
            overlays.append("Open Interest")
        if overlay_vanna:
            overlays.append("VANNA")
        if overlay_gex:
            overlays.append("GEX")
        
        # ========== CALCULAR GAMMA PROFILE PARA AS CURVAS GEPLS ==========
        price_levels, total_gamma, gamma_ex_next, gamma_ex_fri, gamma_flip, vol_trigger = calcular_gamma_profile_completo(
            st.session_state["df_filtrado"], spot
        )
        
        gamma_profile_data = None
        if price_levels is not None:
            gamma_profile_data = {
                'price_levels': price_levels,
                'total_gamma': total_gamma,
                'gamma_ex_next': gamma_ex_next,
                'gamma_ex_fri': gamma_ex_fri
            }
        
        # ========== 🟡 OBTER LISTAS DE LINHAS ==========
        lines_pcp = st.session_state.get("lines_pcp", [])
        lines_int = st.session_state.get("lines_int", [])
        
        # ========== GERAR GRÁFICO (COM LINHAS) ==========
        fig_gamma_points = criar_grafico_gamma_points_overlay(
            df=st.session_state["df_filtrado"],
            spot=spot,
            basis=basis,
            strikes=strikes_calc,
            pivots=pivots,
            normalize=normalize,
            overlays=overlays,
            show_dex=overlay_dex,
            show_gepls=overlay_gepls,
            gamma_profile_data=gamma_profile_data,
            lines_pcp=lines_pcp,
            lines_int=lines_int
        )
        
        render_chart(fig_gamma_points, key="fig_gamma_points")
        
        # ========== 🆕 SEÇÃO DE CONTROLE DE LINHAS ==========
        st.divider()
        st.markdown("### 🎯 Gerenciar Linhas de Strikes (A3)")
        st.caption("Adicione linhas no gráfico para marcar strikes Pcp e Int. O relatório A3 será gerado automaticamente.")

        # ✅ LER VALORES ATUALIZADOS DO SESSION STATE
        lines_pcp = st.session_state.get("lines_pcp", [])
        lines_int = st.session_state.get("lines_int", [])

        # ✅ FORM PARA EVITAR QUE SELECTBOX ATUALIZE O GRÁFICO
        with st.form(key="form_linhas_strikes"):
            # ========== LINHA 1: INPUT + BOTÕES DE ADICIONAR ==========
            col_input, col_btn_pcp, col_btn_int, col_status = st.columns([2, 1, 1, 1])
            
            with col_input:
                # 🆕 Dropdown com strikes disponíveis + opção de digitar
                options = [f"{int(s)} (CVS: {calcular_cvs(s, basis, spot):04d})" for s in strikes_calc]
                
                selected_option = st.selectbox(
                    "📌 Selecione ou digite um strike:",
                    options=["(Digite manualmente abaixo)"] + options,
                    key="strike_select_lines",
                    index=0
                )
                
                # Se escolheu "Digite manualmente", mostra input numérico
                if selected_option == "(Digite manualmente abaixo)":
                    strike_input = st.number_input(
                        "Strike (valor numérico):",
                        min_value=0,
                        max_value=1000000,
                        value=int(spot) if spot else 0,
                        step=10,
                        key="strike_manual_input"
                    )
                    strike_to_add = strike_input
                else:
                    strike_to_add = int(selected_option.split()[0])
            
            with col_btn_pcp:
                pcp_count = len(lines_pcp)
                # ✅ form_submit_button - cada um já submete o form
                btn_pcp_clicked = st.form_submit_button(
                    f"🟡 Adicionar Pcp ({pcp_count}/20)", 
                    use_container_width=True, 
                    type="primary"
                )
            
            with col_btn_int:
                int_count = len(lines_int)
                # ✅ form_submit_button - cada um já submete o form
                btn_int_clicked = st.form_submit_button(
                    f"🟡 Adicionar Int ({int_count}/20)", 
                    use_container_width=True
                )
            
            with col_status:
                total_lines = len(lines_pcp) + len(lines_int)
                if total_lines > 0:
                    st.metric("Total de Linhas", f"{total_lines}")
                else:
                    st.info("Nenhuma linha")
            
            # ✅ PROCESSAR CLIQUES DENTRO DO FORM
            if btn_pcp_clicked:
                adicionar_linha_strike(strike_to_add, 'pcp')
            
            if btn_int_clicked:
                adicionar_linha_strike(strike_to_add, 'int')

        # ========== LINHA 2: LISTA DE LINHAS ADICIONADAS (FORA DO FORM) ==========
        if lines_pcp or lines_int:
            st.divider()
            
            col_pcp_list, col_int_list = st.columns(2)
            
            with col_pcp_list:
                st.markdown("**🟡 Linhas Pcp (Principal)**")
                if lines_pcp:
                    for strike in lines_pcp:
                        cvs = calcular_cvs(strike, basis, spot)
                        col_strike, col_cvs, col_btn = st.columns([2, 2, 1])
                        with col_strike:
                            st.markdown(f"**{int(strike)}**")
                        with col_cvs:
                            st.markdown(f"CVS: {cvs:04d}")
                        with col_btn:
                            if st.button("❌", key=f"rem_pcp_{strike}", 
                                        help=f"Remover linha Pcp {strike}"):
                                remover_linha_strike(strike, 'pcp')
                else:
                    st.caption("Nenhuma linha Pcp adicionada")
            
            with col_int_list:
                st.markdown("**🟡 Linhas Int (Intermediário)**")
                if lines_int:
                    for strike in lines_int:
                        cvs = calcular_cvs(strike, basis, spot)
                        col_strike, col_cvs, col_btn = st.columns([2, 2, 1])
                        with col_strike:
                            st.markdown(f"**{int(strike)}**")
                        with col_cvs:
                            st.markdown(f"CVS: {cvs:04d}")
                        with col_btn:
                            if st.button("❌", key=f"rem_int_{strike}", 
                                        help=f"Remover linha Int {strike}"):
                                remover_linha_strike(strike, 'int')
                else:
                    st.caption("Nenhuma linha Int adicionada")
            
            # Botão limpar todas
            st.divider()
            if st.button("🗑️ Limpar Todas as Linhas", 
                        use_container_width=True, 
                        key="btn_limpar_todas_linhas"):
                limpar_todas_linhas()
                
        # ========== MÉTRICAS ==========
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Spot", f"{spot:.2f}")
        with col2:
            if gamma_flip:
                st.metric("Gamma Flip", f"{gamma_flip:.2f}")
            else:
                st.metric("Gamma Flip", "N/A")
        with col3:
            if vol_trigger:
                st.metric("Vol Trigger", f"{vol_trigger:.2f}")
            else:
                st.metric("Vol Trigger", "N/A")
        
        # ========== LEGENDA DE GRÁFICOS ATIVOS ==========
        ativos = []
        if overlay_dex:
            ativos.append("DEX")
        if overlay_volume:
            ativos.append("Volume")
        if overlay_oi:
            ativos.append("Open Interest")
        if overlay_vanna:
            ativos.append("VANNA")
        if overlay_gex:
            ativos.append("GEX")
        if overlay_gepls:
            ativos.append("GEPLS (Curvas)")
        
        if ativos:
            st.caption(f"📌 Gráficos ativos: {', '.join(ativos)}")
        else:
            st.caption("📌 Nenhum gráfico ativo")

    # ========== ABA 1: TOTAL GAMMA EXPOSURE (BARRAS) ==========
    with tab1:
        st.subheader("📊 Total Gamma Exposure - Barras")
        st.caption(f"Total de strikes no arquivo: {len(strikes_unicos)}")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_barras = criar_grafico_total_gamma_barras(st.session_state["df_filtrado"], spot, basis)
        render_chart(fig_barras, key="fig_barras")

    # ========== ABA 2: GAMMA EXPOSURE PROFILE (CURVAS) ==========
    with tab2:
        st.subheader("📐 Gamma Exposure Profile - Curvas Contínuas")
        st.caption(f"Perfil calculado com todos os {len(strikes_unicos)} strikes do arquivo")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        
        if price_levels is not None:
            fig_curvas = cache_gamma_profile_curvas(
                price_levels=price_levels,
                total_gamma=total_gamma,
                gamma_ex_next=gamma_ex_next,
                gamma_ex_fri=gamma_ex_fri,
                spot=spot,
                basis=basis,
                gamma_flip=gamma_flip,
                vol_trigger=vol_trigger
            )
            render_chart(fig_curvas, key="fig_curvas")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Spot", f"{spot:.2f}")
            with col2:
                if gamma_flip:
                    st.metric("Gamma Flip", f"{gamma_flip:.2f}")
                else:
                    st.metric("Gamma Flip", "N/A")
            with col3:
                if vol_trigger:
                    st.metric("Vol Trigger", f"{vol_trigger:.2f}")
                else:
                    st.metric("Vol Trigger", "N/A")
        else:
            st.error("❌ Erro ao calcular Gamma Profile")

    # ========== ABA 3: TODOS OS GRÁFICOS ==========
    with tab3:
        st.subheader("📈 Todos os Gráficos - Análise Completa")
        st.caption(f"Strikes exibidos: {len(strikes_calc)} (filtrado por {n_strikes} strikes cada lado, step={step})")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_todos = criar_grafico_todos_graficos(strikes_calc, pivots, spot, basis, normalize=normalize)
        render_chart(fig_todos, key="fig_todos")

    # ========== ABA 4: DEX ==========
    with tab4:
        st.subheader("DEX - Delta Exposure")
        st.caption("Exposição Delta por strike - Calls (branco) | Puts (branco)")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_dex = criar_grafico_individual(strikes_calc, pivots, spot, basis, "DEX", normalize=normalize)
        render_chart(fig_dex, key="fig_dex")

    # ========== ABA 5: GEX ==========
    with tab5:
        st.subheader("📈 GEX - Gamma Exposure")
        st.caption("Exposição Gamma por strike - Calls (ciano) | Puts (ciano)")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_gex = criar_grafico_individual(strikes_calc, pivots, spot, basis, "GEX", normalize=normalize)
        render_chart(fig_gex, key="fig_gex")

    # ========== ABA 6: VANNA ==========
    with tab6:
        st.subheader("📊 VANNA")
        st.caption("VANNA por strike - Calls (amarelo) | Puts (fúcsia)")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_vanna = criar_grafico_individual(strikes_calc, pivots, spot, basis, "VANNA", normalize=normalize)
        render_chart(fig_vanna, key="fig_vanna")

    # ========== ABA 7: VOLUME ==========
    with tab7:
        st.subheader("Volume")
        st.caption("Volume por strike - Calls (cinza) | Puts (cinza)")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_vol = criar_grafico_individual(strikes_calc, pivots, spot, basis, "Volume", normalize=normalize)
        render_chart(fig_vol, key="fig_vol")

    # ========== ABA 8: OPEN INTEREST ==========
    with tab8:
        st.subheader("Open Interest")
        st.caption("Open Interest por strike - Calls (azul royal) | Puts (vermelho)")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        fig_oi = criar_grafico_individual(strikes_calc, pivots, spot, basis, "Open Interest", normalize=normalize)
        render_chart(fig_oi, key="fig_oi")

    # ========== ABA 9: DADOS EXPORTADOS ==========
    with tab9:
        st.subheader("📋 Dados Exportados")
        st.caption(f"Dados filtrados: {len(strikes_calc)} strikes")
        st.caption(f"📌 Filtro: {active_expiry_filter}")
        
        strikes_cvs = [calcular_cvs(s, basis, spot) for s in strikes_calc]
        
        df_export = pd.DataFrame({
            'Strike_Original': strikes_calc,
            'Strike_CVS': strikes_cvs,
            'DEX_Call': pivots["DEX"]["Call"].values,
            'DEX_Put': pivots["DEX"]["Put"].values,
            'DEX_Net': pivots["DEX"]["Call"].values + pivots["DEX"]["Put"].values,
            'GEX_Call': pivots["GEX"]["Call"].values,
            'GEX_Put': pivots["GEX"]["Put"].values,
            'GEX_Net': pivots["GEX"]["Call"].values - pivots["GEX"]["Put"].values,
            'OpenInterest_Call': pivots["Open Interest"]["Call"].values,
            'OpenInterest_Put': pivots["Open Interest"]["Put"].values,
            'OpenInterest_Total': pivots["Open Interest"]["Call"].values + pivots["Open Interest"]["Put"].values,
            'Volume_Call': pivots["Volume"]["Call"].values,
            'Volume_Put': pivots["Volume"]["Put"].values,
            'Volume_Total': pivots["Volume"]["Call"].values + pivots["Volume"]["Put"].values,
            'VANNA_Call': pivots["VANNA"]["Call"].values,
            'VANNA_Put': pivots["VANNA"]["Put"].values,
            'VANNA_Net': pivots["VANNA"]["Call"].values - pivots["VANNA"]["Put"].values
        })
        
        st.dataframe(df_export, use_container_width=True, height=400)
        
        col_csv, col_json = st.columns(2)
        with col_csv:
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                "📥 Baixar CSV", csv_data, 
                f"gamma_points_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                "text/csv", use_container_width=True
            )
        with col_json:
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button(
                "📥 Baixar JSON", json_data, 
                f"gamma_points_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                "application/json", use_container_width=True
            )
        
        st.subheader("📊 Estatísticas Rápidas")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.metric("Total DEX Líquido", f"{df_export['DEX_Net'].sum():.2f}")
        with stat_col2:
            st.metric("Total GEX Líquido", f"{df_export['GEX_Net'].sum():.2f}")
        with stat_col3:
            st.metric("Total VANNA Líquido", f"{df_export['VANNA_Net'].sum():.2f}")
        with stat_col4:
            st.metric("Total Open Interest", f"{df_export['OpenInterest_Total'].sum():.0f}")

    # ========== ABA 10: RELATÓRIOS ==========
    with tab10:
        exibir_aba_relatorios()

def exibir_aba_relatorios():
    """
    Exibe a aba de Relatórios com todos os relatórios já pré-gerados
    """
    st.subheader("📊 Relatórios GPHM")
    
    # ========== VERIFICAR SE HÁ DADOS CARREGADOS ==========
    if not st.session_state["dados_carregados"]:
        st.warning("⚠️ Nenhum dado carregado. Carregue um arquivo primeiro para gerar relatórios.")
        return
    
    # ========== VERIFICAR BASIS ==========
    if abs(st.session_state["basis"] - 1.0) < 1e-6:
        st.warning("⚠️ BASIS OF CONVERSION = 1 → Sistema desligado.")
        st.info("📌 Ajuste o BASIS para um valor diferente de 1 para gerar relatórios.")
        st.caption(f"📌 BASIS atual: **{st.session_state['basis']:.2f}**")
        return
    
    # ========== INFORMAR QUE RELATÓRIOS ESTÃO PRONTOS ==========
    a1_pronto = st.session_state.get("relatorio_a1_pronto", False)
    a2_pronto = st.session_state.get("relatorio_a2_pronto", False)
    
    if a1_pronto or a2_pronto:
        st.success("✅ Relatórios prontos para download!")
    else:
        st.warning("⚠️ Relatórios indisponíveis. Verifique o BASIS e os filtros.")
    
    st.caption("📌 Os relatórios são gerados automaticamente quando os dados são carregados ou filtros mudam.")
    st.caption(f"📌 Filtro atual: **{st.session_state['active_expiry_filter']}**")
    st.caption(f"📌 BASIS atual: **{st.session_state['basis']:.2f}**")
    st.caption(f"📌 Strikes disponíveis: **{len(st.session_state.get('strikes_calc', []))}**")
    
    st.markdown("---")
    
    # ========== LINHA 1: RELATÓRIO A1 ==========
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown("### 📄 A1 - Relatório GPHM")
        st.caption("Relatório completo com todas as métricas e pontos de interesse")
    
    with col2:
        if st.button("🔄 Recriar A1", use_container_width=True, key="btn_recriar_a1"):
            with st.spinner("🔄 Recriando relatório A1..."):
                gerar_todos_relatorios()
                st.rerun()
    
    with col3:
        if st.session_state.get("relatorio_a1_pronto", False) and st.session_state.get("relatorio_a1_texto"):
            st.download_button(
                label="📥 Baixar A1",
                data=st.session_state["relatorio_a1_texto"],
                file_name=st.session_state.get("relatorio_a1_nome", "relatorio_a1.txt"),
                mime="text/plain",
                use_container_width=True,
                key="download_a1_aba"
            )
            st.caption("✅ Pronto para download")
        else:
            st.warning("⚠️ Indisponível")
    
    # ========== LINHA 2: RELATÓRIO A2 (LINKADO ABAIXO DO A1) ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown("### 📄 A2 - Relatório GPHM")
        st.caption("Análise com níveis institucionais e pontos de interesse")
    
    with col2:
        if st.button("🔄 Recriar A2", use_container_width=True, key="btn_recriar_a2"):
            with st.spinner("🔄 Recriando relatório A2..."):
                gerar_todos_relatorios()
                st.rerun()
    
    with col3:
        if st.session_state.get("relatorio_a2_pronto", False) and st.session_state.get("relatorio_a2_texto"):
            st.download_button(
                label="📥 Baixar A2",
                data=st.session_state["relatorio_a2_texto"],
                file_name=st.session_state.get("relatorio_a2_nome", "relatorio_a2.txt"),
                mime="text/plain",
                use_container_width=True,
                key="download_a2_aba"
            )
            st.caption("✅ Pronto para download")
        else:
            st.warning("⚠️ Indisponível")
    
    # ========== LINHA 3: RELATÓRIO A3 (🆕 FUNCIONAL) ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        st.markdown("### 📄 A3 - Strikes das Linhas")
        st.caption("Relatório com os strikes marcados como linhas no gráfico Gamma Points")
        
        # 🆕 Mostra quantas linhas estão plotadas
        pcp_count = len(st.session_state.get("lines_pcp", []))
        int_count = len(st.session_state.get("lines_int", []))
        st.caption(f"📌 🟢 Pcp: **{pcp_count}/20** | 🟠 Int: **{int_count}/20**")
        
        # 🆕 Mostra as linhas se houver
        if pcp_count > 0 or int_count > 0:
            with st.expander("📋 Ver strikes das linhas"):
                if pcp_count > 0:
                    pcp_list = st.session_state.get("lines_pcp", [])
                    pcp_str = ", ".join([f"{int(s)}" for s in pcp_list])
                    st.write(f"**🟢 Pcp:** {pcp_str}")
                if int_count > 0:
                    int_list = st.session_state.get("lines_int", [])
                    int_str = ", ".join([f"{int(s)}" for s in int_list])
                    st.write(f"**🟠 Int:** {int_str}")

    with col2:
        if st.button("🔄 Recriar A3", use_container_width=True, key="btn_recriar_a3"):
            with st.spinner("🔄 Recriando relatório A3..."):
                gerar_todos_relatorios()
                st.rerun()

    with col3:
        if st.session_state.get("relatorio_a3_pronto", False) and st.session_state.get("relatorio_a3_texto"):
            st.download_button(
                label="📥 Baixar A3",
                data=st.session_state["relatorio_a3_texto"],
                file_name=st.session_state.get("relatorio_a3_nome", "relatorio_a3.txt"),
                mime="text/plain",
                use_container_width=True,
                key="download_a3_aba"
            )
            st.caption("✅ Pronto para download")
        else:
            if pcp_count > 0 or int_count > 0:
                st.warning("⚠️ Aguardando geração do relatório...")
            else:
                st.info("📌 Adicione linhas na aba 'Gamma Points'")
    
    # ========== LINHA 4: RELATÓRIO A4 ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown("### 📄 A4 - Top 10 por Métrica")
        st.caption("Relatório com os 10 maiores pontos por métrica")
        st.caption("📌 Em desenvolvimento")
    
    with col2:
        st.button("🔄 Recriar A4", use_container_width=True, key="btn_recriar_a4", disabled=True)
    
    with col3:
        st.info("📌 Em breve")
    
    st.markdown("---")
    st.caption("💡 Os relatórios são atualizados automaticamente quando o BASIS ou filtro mudam.")

def gerar_todos_relatorios():
    """
    Gera todos os relatórios automaticamente quando:
    - Dados são carregados
    - BASIS muda para um valor diferente de 1
    - Filtro de vencimento muda
    - Strikes mudam
    - 🆕 Linhas Pcp/Int mudam
    """
    # ========== VERIFICAR CONDIÇÕES PARA GERAR ==========
    if not st.session_state["dados_carregados"]:
        # Limpar relatórios se não há dados
        st.session_state["relatorio_a1_pronto"] = False
        st.session_state["relatorio_a1_texto"] = None
        st.session_state["relatorio_a1_nome"] = None
        st.session_state["relatorio_a2_pronto"] = False
        st.session_state["relatorio_a2_texto"] = None
        st.session_state["relatorio_a2_nome"] = None
        st.session_state["relatorio_a3_pronto"] = False
        st.session_state["relatorio_a3_texto"] = None
        st.session_state["relatorio_a3_nome"] = None
        return
    
    # ========== SE BASIS = 1, LIMPAR RELATÓRIOS ==========
    if abs(st.session_state["basis"] - 1.0) < 1e-6:
        st.session_state["relatorio_a1_pronto"] = False
        st.session_state["relatorio_a1_texto"] = None
        st.session_state["relatorio_a1_nome"] = None
        st.session_state["relatorio_a2_pronto"] = False
        st.session_state["relatorio_a2_texto"] = None
        st.session_state["relatorio_a2_nome"] = None
        st.session_state["relatorio_a3_pronto"] = False
        st.session_state["relatorio_a3_texto"] = None
        st.session_state["relatorio_a3_nome"] = None
        return

    # ========== GERAR RELATÓRIO A1 ==========
    try:
        texto_a1 = gerar_relatorio_a1_streamlit(
            df=st.session_state["df_filtrado"],
            spot=st.session_state["spot"],
            basis=st.session_state["basis"],
            symbol=st.session_state["symbol"],
            active_expiry_filter=st.session_state["active_expiry_filter"],
            strikes=st.session_state["strikes_calc"],
            pivots=st.session_state["pivots"]
        )
        
        if not texto_a1.startswith("⚠️"):
            from datetime import datetime
            import re
            
            data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            simbolo_limpo = re.sub(r'[^\w]', '_', st.session_state["symbol"]).upper()
            filtro_abrev = {
                "ALL Expiry": "ALL",
                "MONTH Expiry": "MONTH",
                "0DTE + 4 Expiry": "0DTE_PLUS_4",
                "0DTE Expiry": "0DTE",
                "0DTE +1 Plus Friday": "0DTE_FRI",
                "0DTE Expiry +1": "0DTE_PLUS1",
                None: "ALL"
            }.get(st.session_state["active_expiry_filter"], "ALL")
            
            nome_a1 = f"WTS_GP_{data_str}_{simbolo_limpo}_{filtro_abrev}_A1.txt"
            st.session_state["relatorio_a1_texto"] = texto_a1
            st.session_state["relatorio_a1_nome"] = nome_a1
            st.session_state["relatorio_a1_pronto"] = True
        else:
            st.session_state["relatorio_a1_pronto"] = False
            st.session_state["relatorio_a1_texto"] = None
            st.session_state["relatorio_a1_nome"] = None
    except Exception as e:
        st.session_state["relatorio_a1_pronto"] = False
        st.session_state["relatorio_a1_texto"] = None
        st.session_state["relatorio_a1_nome"] = None

    # ========== GERAR RELATÓRIO A2 ==========
    try:
        texto_a2, nome_a2 = gerar_relatorio_a2_streamlit(
            df=st.session_state["df_filtrado"],
            spot=st.session_state["spot"],
            basis=st.session_state["basis"],
            symbol=st.session_state["symbol"],
            active_expiry_filter=st.session_state["active_expiry_filter"],
            strikes=st.session_state["strikes_calc"],
            pivots=st.session_state["pivots"]
        )
        
        if texto_a2 is not None and not texto_a2.startswith("⚠️"):
            st.session_state["relatorio_a2_texto"] = texto_a2
            st.session_state["relatorio_a2_nome"] = nome_a2
            st.session_state["relatorio_a2_pronto"] = True
        else:
            st.session_state["relatorio_a2_pronto"] = False
            st.session_state["relatorio_a2_texto"] = None
            st.session_state["relatorio_a2_nome"] = None
    except Exception as e:
        st.session_state["relatorio_a2_pronto"] = False
        st.session_state["relatorio_a2_texto"] = None
        st.session_state["relatorio_a2_nome"] = None

    # ========== 🆕 GERAR RELATÓRIO A3 (AGORA FUNCIONAL) ==========
    try:
        texto_a3, nome_a3 = gerar_relatorio_a3_streamlit(
            df=st.session_state["df_filtrado"],
            spot=st.session_state["spot"],
            basis=st.session_state["basis"],
            symbol=st.session_state["symbol"],
            active_expiry_filter=st.session_state["active_expiry_filter"],
            strikes=st.session_state["strikes_calc"],
            pivots=st.session_state["pivots"]
        )
        
        if texto_a3 is not None and not texto_a3.startswith("⚠️"):
            st.session_state["relatorio_a3_texto"] = texto_a3
            st.session_state["relatorio_a3_nome"] = nome_a3
            st.session_state["relatorio_a3_pronto"] = True
        else:
            st.session_state["relatorio_a3_pronto"] = False
            st.session_state["relatorio_a3_texto"] = None
            st.session_state["relatorio_a3_nome"] = None
    except Exception as e:
        st.session_state["relatorio_a3_pronto"] = False
        st.session_state["relatorio_a3_texto"] = None
        st.session_state["relatorio_a3_nome"] = None


# =============================================================================
# FUNÇÃO MAIN (PRINCIPAL)
# =============================================================================
def main():
    """Função principal do Streamlit"""
    
    # ========== LIMPAR ARQUIVOS DE MÍDIA ÓRFÃOS ==========
    if "media_cleared" not in st.session_state:
        try:
            st.cache_data.clear()
            st.cache_resource.clear()
        except:
            pass
        st.session_state["media_cleared"] = True
    
    # ========== INICIALIZAR ESTADO DA SESSÃO ==========
    if "download_em_andamento" not in st.session_state:
        st.session_state["download_em_andamento"] = False
    
    if "download_resultados" not in st.session_state:
        st.session_state["download_resultados"] = None
    
    if "arquivo_para_carregar" not in st.session_state:
        st.session_state["arquivo_para_carregar"] = None
    
    # ========== FILTROS ==========
    if "active_expiry_filter" not in st.session_state:
        st.session_state["active_expiry_filter"] = "ALL Expiry"
    
    if "n_strikes" not in st.session_state:
        st.session_state["n_strikes"] = 40
    
    if "step" not in st.session_state:
        st.session_state["step"] = 1
    
    if "normalizacao_ativa" not in st.session_state:
        st.session_state["normalizacao_ativa"] = False
    
    # ========== BASIS ==========
    if "basis" not in st.session_state:
        st.session_state["basis"] = 1.0
    
    # ========== RELATÓRIOS ==========
    if "relatorio_a1_pronto" not in st.session_state:
        st.session_state["relatorio_a1_pronto"] = False
        st.session_state["relatorio_a1_texto"] = None
        st.session_state["relatorio_a1_nome"] = None


    # Adicionar no início da main(), após as outras inicializações
    if "relatorio_a2_pronto" not in st.session_state:
        st.session_state["relatorio_a2_pronto"] = False
        st.session_state["relatorio_a2_texto"] = None
        st.session_state["relatorio_a2_nome"] = None

    # ========== 🆕 LINHAS DE STRIKES (NOVO SISTEMA) ==========
    if "lines_pcp" not in st.session_state:
        st.session_state["lines_pcp"] = []  # Strikes com linhas Pcp (verde)
    
    if "lines_int" not in st.session_state:
        st.session_state["lines_int"] = []  # Strikes com linhas Int (laranja)
    
    # ========== RELATÓRIOS ==========
    if "relatorio_a1_pronto" not in st.session_state:
        st.session_state["relatorio_a1_pronto"] = False
        st.session_state["relatorio_a1_texto"] = None
        st.session_state["relatorio_a1_nome"] = None
    
    if "relatorio_a2_pronto" not in st.session_state:
        st.session_state["relatorio_a2_pronto"] = False
        st.session_state["relatorio_a2_texto"] = None
        st.session_state["relatorio_a2_nome"] = None
    
    # 🆕 A3 AGORA FUNCIONAL
    if "relatorio_a3_pronto" not in st.session_state:
        st.session_state["relatorio_a3_pronto"] = False
        st.session_state["relatorio_a3_texto"] = None
        st.session_state["relatorio_a3_nome"] = None
    
    # ========== DADOS CARREGADOS ==========
    if "dados_carregados" not in st.session_state:
        st.session_state["dados_carregados"] = False
        st.session_state["df_original"] = None
        st.session_state["df_filtrado"] = None
        st.session_state["spot"] = None
        st.session_state["symbol"] = None
        st.session_state["strikes_calc"] = None
        st.session_state["pivots"] = None
        st.session_state["strikes_unicos"] = None
    
    # ========== CARREGAR ARQUIVO PENDENTE ==========
    if st.session_state.get("arquivo_para_carregar"):
        arquivo = st.session_state["arquivo_para_carregar"]
        if os.path.exists(arquivo):
            with open(arquivo, 'rb') as f:
                file_content = f.read()
                st.session_state["upload_automatico"] = file_content
        del st.session_state["arquivo_para_carregar"]
    
    if not verificar_acesso():
        return
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        # ========== WTS GAMMA POINTS ==========
        st.markdown("""
        <div style="text-align: center; padding: 10px 0; border-bottom: 1px solid #444; margin-bottom: 15px;">
            <span style="color: #000000; font-size: 22px; font-weight: bold; letter-spacing: 2px;">⚡ WTS GAMMA POINTS</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.success(f"✅ Logado como: {st.session_state.get('email_usuario')}")
        
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["dados_carregados"] = False
            st.session_state["relatorio_a1_pronto"] = False
            st.rerun()
        
        st.divider()
        
        # ========== DOWNLOAD AUTOMÁTICO ==========
        st.subheader("📥 Download Automático")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 SPX + Ativos", use_container_width=True):
                iniciar_download_spx_completo()
        with col2:
            if st.button("📁 Download Manual", use_container_width=True):
                abrir_dialogo_download_manual()
        
        if st.session_state.get("download_em_andamento", False):
            st.info("⏳ Download em andamento...")
        
        st.caption("Ativos: SPX, NDX, EWZ, VALE, PBR, SPY, USO, EEM, ABEV, ITUB")
        st.divider()
        
        # ========== BASIS ==========
        st.subheader("🔄 BASIS OF CONVERSION")
        
        with st.form(key="basis_form"):
            basis_input = st.number_input(
                "Basis of Conversion (D-1)",
                value=st.session_state["basis"],
                min_value=0.01,
                max_value=1000000.0,
                step=1.0,
                format="%.2f"
            )
            
            submitted_basis = st.form_submit_button("Aplicar BASIS", use_container_width=True, type="primary")
            
            if submitted_basis:
                if basis_input != st.session_state["basis"]:
                    st.session_state["basis"] = basis_input
                    with st.spinner("🔄 Processando BASIS e gerando relatórios..."):
                        if st.session_state["dados_carregados"]:
                            atualizar_dados_com_filtro()
                            gerar_todos_relatorios()
                    st.success(f"✅ BASIS atualizado para {basis_input:.2f}")
                    st.rerun()
        
        if abs(st.session_state["basis"] - 1.0) < 1e-6:
            st.warning("⚠️ BASIS = 1 → Sistema desligado")
            st.session_state["relatorio_a1_pronto"] = False
            st.session_state["relatorio_a1_texto"] = None
            st.session_state["relatorio_a1_nome"] = None
        else:
            st.success(f"✅ BASIS = {st.session_state['basis']:.2f} → Sistema ativo")
            if st.session_state["dados_carregados"] and not st.session_state.get("relatorio_a1_pronto", False):
                gerar_todos_relatorios()
        
        st.divider()
        
        # ========== FILTRO DE VENCIMENTO ==========
        st.subheader("📅 Filtro de Vencimento")
        
        with st.form(key="filtro_form"):
            opcoes_filtro = [
                "ALL Expiry",
                "MONTH Expiry",
                "0DTE + 4 Expiry",
                "0DTE Expiry",
                "0DTE +1 Plus Friday",
                "0DTE Expiry +1"
            ]
            
            indice_atual = 0
            if st.session_state["active_expiry_filter"] in opcoes_filtro:
                indice_atual = opcoes_filtro.index(st.session_state["active_expiry_filter"])
            
            filtro_selecionado = st.selectbox(
                "Selecione o filtro",
                opcoes_filtro,
                index=indice_atual
            )
            
            submitted = st.form_submit_button("Aplicar", use_container_width=True, type="primary")
            
            if submitted:
                if filtro_selecionado != st.session_state["active_expiry_filter"]:
                    st.session_state["active_expiry_filter"] = filtro_selecionado
                    if st.session_state["dados_carregados"]:
                        with st.spinner("🔄 Aplicando filtro e atualizando relatórios..."):
                            atualizar_dados_com_filtro()
                            gerar_todos_relatorios()
                    st.rerun()
        
        st.caption(f"📌 Filtro: **{st.session_state['active_expiry_filter']}**")
        st.divider()
        
        # ========== CONTROLES ADICIONAIS ==========
        st.subheader("🎯 Controle de Strikes")
        
        with st.form(key="strikes_form"):
            n_strikes = st.number_input(
                "Strikes cada lado", 
                min_value=5, 
                max_value=100, 
                value=st.session_state["n_strikes"]
            )
            
            step = st.number_input(
                "Pular strikes", 
                min_value=1, 
                max_value=20, 
                value=st.session_state["step"]
            )
            
            submitted_strikes = st.form_submit_button("Aplicar", use_container_width=True)
            
            if submitted_strikes:
                st.session_state["n_strikes"] = n_strikes
                st.session_state["step"] = step
                if st.session_state["dados_carregados"]:
                    with st.spinner("🔄 Atualizando strikes e relatórios..."):
                        atualizar_dados_com_filtro()
                        gerar_todos_relatorios()
                st.rerun()
        
        st.divider()
        
        # ========== OPÇÕES ==========
        st.subheader("📊 Opções")
        
        normalize = st.checkbox("Normalizar Eixos", value=st.session_state["normalizacao_ativa"])
        if normalize != st.session_state["normalizacao_ativa"]:
            st.session_state["normalizacao_ativa"] = normalize
            if st.session_state["dados_carregados"]:
                st.rerun()
        
        st.divider()
        st.caption("⚡ Cache ativo")
        
        if st.session_state["dados_carregados"]:
            st.caption(f"📌 Strikes: {len(st.session_state.get('strikes_calc', []))}")
            st.caption(f"📌 BASIS: {st.session_state['basis']:.2f}")
            if st.session_state.get("relatorio_a1_pronto", False):
                st.caption("📌 Relatório A1: ✅ Pronto")

    # ========== MAIN CONTENT ==========
    
    # ========== TÍTULO E UPLOAD EM COLUNAS ==========
    col_title, col_upload = st.columns([1, 2])
    
    with col_title:
        st.title("📊 Gamma Points Dashboard")
    
    with col_upload:
        uploaded_file = st.file_uploader("📂 Carregar arquivo CSV (formato CBOE)", type=['csv'], label_visibility="collapsed")
    
    # ========== PROCESSAR UPLOAD ==========
    if uploaded_file is not None:
        with st.spinner("Processando arquivo..."):
            symbol, spot, data_str, df = cache_leitura_csv(uploaded_file.getvalue())
            
            if df is not None and not df.empty:
                st.success(f"✅ {symbol} | Spot: {spot:.2f} | Data: {data_str}")
                
                st.session_state["dados_carregados"] = True
                st.session_state["df_original"] = df
                st.session_state["spot"] = spot
                st.session_state["basis"] = st.session_state.get("basis", 1.0)
                st.session_state["symbol"] = symbol
                
                strikes_unicos = sorted(df['Strike'].unique())
                st.session_state["strikes_unicos"] = strikes_unicos
                
                with st.spinner("🔄 Aplicando filtro inicial..."):
                    atualizar_dados_com_filtro()
                
                if st.session_state["strikes_calc"] and st.session_state["pivots"]:
                    with st.spinner("🔄 Gerando relatórios..."):
                        gerar_todos_relatorios()
                    exibir_abas_graficos()
                else:
                    st.warning("⚠️ Nenhum strike selecionado. Ajuste os filtros.")
            else:
                st.error("Erro ao processar o arquivo. Verifique o formato do CSV.")
    else:
        # ========== SE NÃO HOUVER UPLOAD ==========
        if st.session_state.get("upload_automatico"):
            uploaded_file = st.session_state["upload_automatico"]
            st.session_state["upload_automatico"] = None
            st.rerun()
        
        if st.session_state["dados_carregados"]:
            st.info(f"📁 Arquivo carregado: {st.session_state['symbol']} | Spot: {st.session_state['spot']:.2f}")
            
            if st.session_state["strikes_calc"] and st.session_state["pivots"]:
                if not st.session_state.get("relatorio_a1_pronto", False):
                    with st.spinner("🔄 Gerando relatórios..."):
                        gerar_todos_relatorios()
                exibir_abas_graficos()
            else:
                st.warning("⚠️ Nenhum strike selecionado. Ajuste os filtros.")
        else:
            st.info("📂 Aguardando upload do arquivo CSV...")
            st.markdown("""
            ### 📋 Formato esperado do arquivo:
            - Arquivo CSV no formato CBOE
            - Deve conter colunas: ExpirationDate, Strike, CallDelta, CallGamma, CallOpenInt, etc.
            - O arquivo deve ter o cabeçalho padrão da CBOE
            
            ### 🔄 Ou use o Download Automático na barra lateral
            """)
# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    main()