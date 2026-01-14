import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os

# Importaciones de tus módulos locales
from utils.sheets_connector import SheetsConnector
from utils.lifecycle_calculator import LifecycleCalculator
from utils.gemini_analyzer import GeminiAnalyzer
from utils.user_manager import UserManager

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Concremag - Gestión de Activos",
    page_icon="🏗️",
    layout="wide"
)

# ============================================
# FUNCIONES DE UTILIDAD (SECRETS & CACHE)
# ============================================

def get_secret(key_name):
    """
    Busca una clave en st.secrets, ya sea en la raíz o dentro 
    de la sección [gcp_service_account] donde suelen quedar agrupadas.
    """
    # 1. Buscar en la raíz
    if key_name in st.secrets:
        return st.secrets[key_name]
    
    # 2. Buscar dentro de gcp_service_account (caso común al copiar/pegar toml)
    if "gcp_service_account" in st.secrets:
        if key_name in st.secrets["gcp_service_account"]:
            return st.secrets["gcp_service_account"][key_name]
            
    # 3. Buscar en variables de entorno (para local/docker)
    return os.getenv(key_name)

# Recuperar credenciales de forma robusta
SHEET_ID = get_secret("GOOGLE_SHEET_ID")
API_KEY = get_secret("GEMINI_API_KEY")

@st.cache_data(ttl=600, show_spinner=False)
def load_data_from_sheets():
    """
    Carga los datos y los guarda en memoria por 10 minutos (ttl=600).
    Esto evita llamadas excesivas a la API de Google.
    """
    if not SHEET_ID:
        return None, None, None
    
    try:
        # Instanciamos el conector solo para la carga
        conn = SheetsConnector(spreadsheet_id=SHEET_ID)
        df_a = conn.get_data("Activos")
        df_m = conn.get_data("Mantenimiento")
        df_c = conn.get_data("Costos_Referencia")
        return df_a, df_m, df_c
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ============================================
# GESTIÓN DE TEMA (DARK/LIGHT)
# ============================================
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# CSS Dinámico
if st.session_state.theme == 'dark':
    bg_color = "#2B2B2B"
    text_color = "#E0E0E0"
    card_bg = "#3A3A3A"
    sidebar_bg = "#1E1E1E"
    accent_color = "#00D4FF"
    alert_bg = "rgba(255, 193, 7, 0.2)"
else:
    bg_color = "#F5F5F5"
    text_color = "#2B2B2B"
    card_bg = "#FFFFFF"
    sidebar_bg = "#E8E8E8"
    accent_color = "#0077B6"
    alert_bg = "rgba(255, 193, 7, 0.6)"

st.markdown(f"""
<style>
    .stApp {{ background-color: {bg_color}; }}
    [data-testid="stMetricValue"] {{ font-size: 2.8rem; font-weight: 700; color: {accent_color}; }}
    [data-testid="stMetricLabel"] {{ color: {text_color}; font-size: 0.9rem; text-transform: uppercase; }}
    h1 {{ color: {accent_color} !important; font-size: 2.5rem !important; font-weight: 700 !important; }}
    h2 {{ color: {text_color} !important; font-size: 1.8rem !important; }}
    h3 {{ color: {accent_color} !important; font-size: 1.3rem !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg}; border-right: 2px solid {accent_color}; }}
    .stButton>button {{
        background: linear-gradient(90deg, {accent_color} 0%, #00A8CC 100%);
        color: {bg_color}; font-weight: bold; border-radius: 8px; border: none;
        padding: 0.6rem 2rem; box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
        transition: all 0.3s; text-transform: uppercase; font-size: 0.9rem;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 212, 255, 0.5); }}
    .dataframe {{ border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); background-color: {card_bg} !important; }}
    .streamlit-expanderHeader {{ background-color: {card_bg}; border-left: 4px solid {accent_color}; border-radius: 4px; font-weight: 600; }}
    p, span, div, label {{ color: {text_color}; }}
    /* Corrección de visibilidad para Alertas */
    .stAlert {{ background-color: {alert_bg} !important; border: 1px solid #FFC107 !important; color: #FFC107 !important; }}
    .stAlert p {{ color: #FFD93D !important; font-weight: 500; }}
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    st.markdown("# 🏗️")
with col2:
    st.markdown("# Concremag S.A.")
    st.markdown("### 🤖 Sistema Inteligente de Gestión de Activos")
with col3:
    theme_icon = "🌙" if st.session_state.theme == 'dark' else "☀️"
    if st.button(theme_icon, key="theme_toggle"):
        toggle_theme()
        st.rerun()

st.markdown("---")

# ============================================
# AUTENTICACIÓN
# ============================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None

if not st.session_state.authenticated:
    st.title("🔐 Acceso al Sistema")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="tu@email.com")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Tu contraseña")
            submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            
            if submit:
                if not SHEET_ID:
                    st.error("❌ Error de Configuración: No se encontró GOOGLE_SHEET_ID en Secrets.")
                else:
                    try:
                        # Usamos conexión directa sin cache para login (seguridad)
                        temp_conn = SheetsConnector(spreadsheet_id=SHEET_ID)
                        user_mgr = UserManager(temp_conn)
                        
                        if user_mgr.verify_password(email, password):
                            user_info = user_mgr.get_user_info(email)
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_name = user_info['name']
                            st.success("✅ Acceso concedido")
                            st.rerun()
                        else:
                            st.error("❌ Email o contraseña incorrectos")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {str(e)}")
    st.stop()

# Usuario logueado
user_email = st.session_state.user_email
user_name = st.session_state.user_name

st.caption(f"👤 {user_name} ({user_email})")
st.markdown("---")

# ============================================
# INICIALIZAR LÓGICA DE NEGOCIO
# ============================================
try:
    calculator = LifecycleCalculator()
    gemini_analyzer = GeminiAnalyzer(api_key=API_KEY) if API_KEY else None

except Exception as e:
    st.error(f"❌ Error al inicializar módulos: {str(e)}")
    st.stop()

# ============================================
# SIDEBAR
# ============================================
st.sidebar.title("📊 Navegación")

if st.sidebar.button("🔄 Recargar Datos", type="primary"):
    # Limpiamos cache para forzar recarga fresca de Google Sheets
    load_data_from_sheets.clear()
    st.rerun()

chile_tz = pytz.timezone('America/Punta_Arenas')
ultima_actualizacion = datetime.now(chile_tz).strftime("%d/%m/%Y - %H:%M:%S")
st.sidebar.caption(f"🕒 Última actualización:\n{ultima_actualizacion}")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.rerun()

st.sidebar.markdown("---")

view_mode = st.sidebar.radio(
    "Selecciona una vista",
    ["Dashboard", "Acciones Prioritarias", "Detalle por Activo", "Análisis IA"]
)

# ============================================
# CARGA DE DATOS (CON CACHE)
# ============================================
with st.spinner("🔄 Obteniendo datos de flota..."):
    df_activos, df_mantenimiento, df_costos_ref = load_data_from_sheets()

if df_activos is None or df_activos.empty:
    st.warning("⚠️ No se pudieron cargar los datos o la hoja 'Activos' está vacía.")
    st.stop()

# Calcular métricas una sola vez
df = calculator.calcular_metricas_completas(df_activos, df_mantenimiento, df_costos_ref)

# ============================================
# VISTAS PRINCIPALES
# ============================================

# --- VISTA 1: DASHBOARD ---
if view_mode == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚛 Total Activos", len(df))
    with col2:
        critical = len(df[df['health_score'] < 40])
        st.metric("🔴 Críticos", critical, delta=f"-{critical}" if critical > 0 else "0", delta_color="inverse")
    with col3:
        avg_age = df['edad_anos'].mean()
        st.metric("📅 Edad Promedio", f"{avg_age:.1f} años")
    with col4:
        next_year = len(df[df['horizonte_meses'] <= 12])
        st.metric("⏰ Acción <12 meses", next_year)

    st.markdown("---")
    st.subheader("📊 Estado de Activos")

    display_df = df[['id_activo', 'tipo_equipo', 'marca', 'modelo', 'edad_anos', 
                      'health_score', 'horizonte_meses', 'accion']].copy()
    display_df['health_score'] = display_df['health_score'].round(1)
    display_df['horizonte_meses'] = display_df['horizonte_meses'].round(0)
    
    def color_health(val):
        if val < 40: return 'background-color: #4A1F1F; color: #FF6B6B'
        elif val < 70: return 'background-color: #4A3F1F; color: #FFD93D'
        else: return 'background-color: #1F4A2F; color: #6BCF7F'
    
    try:
        styled_df = display_df.style.applymap(color_health, subset=['health_score'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    except:
        st.dataframe(display_df, use_container_width=True, height=400)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución por Tipo")
        st.bar_chart(df['tipo_equipo'].value_counts())
    with col2:
        st.subheader("Health Score Promedio")
        st.bar_chart(df.groupby('tipo_equipo')['health_score'].mean().sort_values())

# --- VISTA 2: ACCIONES PRIORITARIAS ---
elif view_mode == "Acciones Prioritarias":
    st.subheader("🚨 Acciones Prioritarias")
    df_recomendaciones = calculator.priorizar_flota(df)

    col1, col2, col3 = st.columns(3)
    with col1:
        total_criticos = len(df_recomendaciones[df_recomendaciones['prioridad'] <= 2])
        st.metric("🔴 Críticos/Urgentes", total_criticos)
    with col2:
        impacto_total = df_recomendaciones['impacto_economico_clp'].sum()
        st.metric("💰 Impacto Total", f"${impacto_total:,.0f}")
    with col3:
        proximos_6m = len(df_recomendaciones[df_recomendaciones['horizonte_meses'] <= 6])
        st.metric("⏰ Acción 6 meses", proximos_6m)

    st.markdown("---")

    for idx, rec in df_recomendaciones.iterrows():
        emoji = "🔴" if rec['prioridad'] == 1 else "🟠" if rec['prioridad'] == 2 else "🟡" if rec['prioridad'] == 3 else "🟢"
        with st.expander(f"{emoji} {rec['accion']} - {rec['id_activo']} ({rec['tipo_equipo']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Razón:** {rec['razon']}")
                st.write(f"**Horizonte:** {rec['horizonte_meses']} meses")
            with col2:
                st.write(f"**Impacto:** ${rec['impacto_economico_clp']:,.0f} CLP")
                st.write(f"**Prioridad:** {rec['prioridad']}")
            st.info(rec['detalle'])

# --- VISTA 3: DETALLE POR ACTIVO ---
elif view_mode == "Detalle por Activo":
    st.subheader("🔍 Análisis Detallado")
    selected_asset = st.selectbox(
        "Selecciona un activo",
        df['id_activo'].tolist(),
        format_func=lambda x: f"{x} - {df[df['id_activo']==x]['tipo_equipo'].values[0]}"
    )
    asset_data = df[df['id_activo'] == selected_asset].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💚 Health Score", f"{asset_data['health_score']:.1f}/100")
    with col2:
        st.metric("⏰ Horizonte", f"{asset_data['horizonte_meses']:.0f} meses")
    with col3:
        st.metric("📅 Edad", f"{asset_data['edad_anos']:.1f} años")

    st.markdown("---")
    st.subheader("📋 Información Completa")
    info_cols = st.columns(2)
    with info_cols[0]:
        st.write(f"**Tipo:** {asset_data['tipo_equipo']}")
        st.write(f"**Marca:** {asset_data['marca']}")
        st.write(f"**Modelo:** {asset_data['modelo']}")
        st.write(f"**Año:** {asset_data['ano_compra']}")
    with info_cols[1]:
        st.write(f"**Horómetro:** {asset_data['horometro_actual']:,.0f} hrs")
        st.write(f"**Costo Mantención:** ${asset_data['costo_mantencion_ultimo_ano']:,.0f}")
        st.write(f"**Valor Residual:** ${asset_data['valor_residual_estimado']:,.0f}")
        st.write(f"**RUL:** {asset_data['rul_horas']:,.0f} hrs")

    st.markdown("---")
    st.subheader("💡 Recomendación")
    st.markdown(f"### {asset_data['accion']}")
    st.write(f"**Razón:** {asset_data['razon']}")
    st.info(asset_data['detalle'])

    st.markdown("---")
    st.subheader("🔧 Historial de Mantenimiento")
    mant_activo = df_mantenimiento[df_mantenimiento['id_activo'] == selected_asset]
    if not mant_activo.empty:
        st.dataframe(mant_activo, use_container_width=True, height=300)
    else:
        st.info("No hay registros de mantenimiento")

# --- VISTA 4: ANÁLISIS IA ---
elif view_mode == "Análisis IA":
    st.subheader("🤖 Análisis con AI (Gemini)")
    
    if not gemini_analyzer:
        st.warning("""
        ⚠️ **No se ha detectado la GEMINI_API_KEY.**
        
        Verifica en tu `.streamlit/secrets.toml` que la clave esté correcta. 
        Si usas un bloque `[gcp_service_account]`, asegúrate de que la API KEY esté definida.
        """)
        st.stop()

    analysis_type = st.radio("Tipo de análisis", ["Resumen Ejecutivo", "Activo Específico", "Pregunta Personalizada"])

    if analysis_type == "Resumen Ejecutivo":
        if st.button("🚀 Generar Resumen", type="primary"):
            with st.spinner("Gemini está analizando toda la flota..."):
                try:
                    summary = gemini_analyzer.generate_executive_summary(df_activos, df_mantenimiento, df_costos_ref)
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"Error en Gemini: {str(e)}")

    elif analysis_type == "Activo Específico":
        selected_asset = st.selectbox("Selecciona un activo para analizar", df['id_activo'].tolist())
        if st.button("🔍 Analizar Activo", type="primary"):
            asset_data = df[df['id_activo'] == selected_asset].iloc[0]
            with st.spinner(f"Analizando el activo {selected_asset}..."):
                try:
                    analysis = gemini_analyzer.analyze_asset(asset_data, df_mantenimiento, df_costos_ref)
                    st.markdown(analysis)
                except Exception as e:
                    st.error(f"Error en Gemini: {str(e)}")

    else:
        question = st.text_area("Escribe tu pregunta sobre la flota", placeholder="Ej: ¿Qué camiones tienen un costo de mantenimiento superior al promedio?")
        if st.button("💬 Consultar", type="primary") and question:
            with st.spinner("Consultando a la base de conocimientos..."):
                try:
                    answer = gemini_analyzer.custom_query(df, df_mantenimiento, df_costos_ref, question)
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"Error en Gemini: {str(e)}")

st.markdown("---")
st.caption("Concremag S.A. - Sistema de Gestión de Activos | Powered by Gemini AI")
