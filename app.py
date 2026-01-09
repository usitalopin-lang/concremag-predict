import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets_connector import SheetsConnector
from utils.lifecycle_calculator import LifecycleCalculator
from utils.gemini_analyzer import GeminiAnalyzer

# Configuración de página
st.set_page_config(page_title="Concremag - Gestión de Activos", page_icon="🏗️", layout="wide")

# CSS Personalizado para look PRO
st.markdown("""
<style>
    /* Fondo con gradiente */
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }

    /* Tarjetas de métricas más atractivas */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FFD700;
    }

    /* Títulos más impactantes */
    h1 {
        color: #FFD700 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-size: 3rem !important;
    }

    h2, h3 {
        color: #FFA500 !important;
    }

    /* Sidebar más elegante */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }

    /* Botones más llamativos */
    .stButton>button {
        background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }

    /* Tablas más profesionales */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header con logo y diseño PRO
col1, col2 = st.columns([1, 5])
with col1:
    st.markdown("# 🏗️")
with col2:
    st.markdown("# Concremag S.A.")
    st.markdown("### 🤖 Sistema Inteligente de Gestión de Activos")

st.markdown("---")

# Inicializar conexiones
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    GOOGLE_SHEET_ID = st.secrets.get("GOOGLE_SHEET_ID")

    sheets_conn = SheetsConnector(spreadsheet_id=GOOGLE_SHEET_ID)
    calculator = LifecycleCalculator()
    gemini_analyzer = GeminiAnalyzer(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

except Exception as e:
    st.error(f"❌ Error al inicializar conexiones: {str(e)}")
    st.stop()

# Sidebar
st.sidebar.title("📊 Navegación")
view_mode = st.sidebar.radio(
    "Selecciona una vista",
    ["Dashboard", "Acciones Prioritarias", "Detalle por Activo", "Análisis IA"]
)

# Cargar datos
try:
    with st.spinner("🔄 Cargando datos desde Google Sheets..."):
        df_activos = sheets_conn.get_data("Activos")
        df_mantenimiento = sheets_conn.get_data("Mantenimiento")
        df_costos_ref = sheets_conn.get_data("Costos_Referencia")

    if df_activos.empty:
        st.warning("⚠️ No hay datos en la hoja 'Activos'. Por favor, agrega información de activos.")
        st.stop()

    # Calcular métricas consolidadas
    df = calculator.calcular_metricas_completas(df_activos, df_mantenimiento, df_costos_ref)

    # DASHBOARD
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

        # Tabla principal
        st.subheader("📊 Estado de Activos")

        display_df = df[['id_activo', 'tipo_equipo', 'marca', 'modelo', 'edad_anos', 
                         'health_score', 'horizonte_meses', 'accion']].copy()

        # Formatear
        display_df['health_score'] = display_df['health_score'].round(1)
        display_df['horizonte_meses'] = display_df['horizonte_meses'].round(0)

        # Colorear
        def color_health(val):
            if val < 40:
                return 'background-color: #ffcccc'
            elif val < 70:
                return 'background-color: #fff4cc'
            else:
                return 'background-color: #ccffcc'

        try:
            styled_df = display_df.style.applymap(color_health, subset=['health_score'])
            st.dataframe(styled_df, use_container_width=True, height=400)
        except:
            st.dataframe(display_df, use_container_width=True, height=400)

        # Gráficos
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribución por Tipo")
            tipo_counts = df['tipo_equipo'].value_counts()
            st.bar_chart(tipo_counts)

        with col2:
            st.subheader("Health Score Promedio por Tipo")
            health_by_type = df.groupby('tipo_equipo')['health_score'].mean().sort_values()
            st.bar_chart(health_by_type)

    # ACCIONES PRIORITARIAS
    elif view_mode == "Acciones Prioritarias":
        st.subheader("🚨 Acciones Prioritarias - Ranking de Urgencia")

        # Generar recomendaciones priorizadas
        df_recomendaciones = calculator.priorizar_flota(df)

        # Métricas de impacto
        col1, col2, col3 = st.columns(3)
        with col1:
            total_criticos = len(df_recomendaciones[df_recomendaciones['prioridad'] <= 2])
            st.metric("🔴 Críticos/Urgentes", total_criticos)
        with col2:
            impacto_total = df_recomendaciones['impacto_economico_clp'].sum()
            st.metric("💰 Impacto Económico Total", f"${impacto_total:,.0f}")
        with col3:
            proximos_6m = len(df_recomendaciones[df_recomendaciones['horizonte_meses'] <= 6])
            st.metric("⏰ Acción en 6 meses", proximos_6m)

        st.markdown("---")

        # Mostrar top activos críticos
        for idx, rec in df_recomendaciones.iterrows():
            if rec['prioridad'] == 1:
                emoji = "🔴"
            elif rec['prioridad'] == 2:
                emoji = "🟠"
            elif rec['prioridad'] == 3:
                emoji = "🟡"
            else:
                emoji = "🟢"

            with st.expander(f"{emoji} {rec['accion']} - {rec['id_activo']} ({rec['tipo_equipo']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Razón:** {rec['razon']}")
                    st.write(f"**Horizonte:** {rec['horizonte_meses']} meses")
                with col2:
                    st.write(f"**Impacto Económico:** ${rec['impacto_economico_clp']:,.0f} CLP")
                    st.write(f"**Prioridad:** {rec['prioridad']}")
                st.info(rec['detalle'])

    # DETALLE POR ACTIVO
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
            st.metric("⏰ Horizonte de Acción", f"{asset_data['horizonte_meses']:.0f} meses")
        with col3:
            st.metric("📅 Edad", f"{asset_data['edad_anos']:.1f} años")

        st.markdown("---")

        st.subheader("📋 Información Completa")
        info_cols = st.columns(2)

        with info_cols[0]:
            st.write(f"**Tipo:** {asset_data['tipo_equipo']}")
            st.write(f"**Marca:** {asset_data['marca']}")
            st.write(f"**Modelo:** {asset_data['modelo']}")
            st.write(f"**Año Compra:** {asset_data['ano_compra']}")

        with info_cols[1]:
            st.write(f"**Horómetro Actual:** {asset_data['horometro_actual']:,.0f} hrs")
            st.write(f"**Costo Mantención (último año):** ${asset_data['costo_mantencion_ultimo_ano']:,.0f}")
            st.write(f"**Valor Residual:** ${asset_data['valor_residual_estimado']:,.0f}")
            st.write(f"**RUL (Vida Restante):** {asset_data['rul_horas']:,.0f} hrs")

        st.markdown("---")
        st.subheader("💡 Recomendación")

        st.markdown(f"### {asset_data['accion']}")
        st.write(f"**Razón:** {asset_data['razon']}")
        st.info(asset_data['detalle'])

        # Historial de mantenimiento
        st.markdown("---")
        st.subheader("🔧 Historial de Mantenimiento")
        mant_activo = df_mantenimiento[df_mantenimiento['id_activo'] == selected_asset]
        if not mant_activo.empty:
            st.dataframe(mant_activo, use_container_width=True)
        else:
            st.info("No hay registros de mantenimiento para este activo.")

    # ANÁLISIS IA
    elif view_mode == "Análisis IA":
        st.subheader("🤖 Análisis con Gemini AI")

        if not gemini_analyzer:
            st.warning("⚠️ Configura GEMINI_API_KEY en Secrets para activar esta función.")
            st.stop()

        analysis_type = st.radio(
            "Tipo de análisis",
            ["Resumen Ejecutivo", "Activo Específico", "Pregunta Personalizada"]
        )

        if analysis_type == "Resumen Ejecutivo":
            if st.button("🚀 Generar Resumen Ejecutivo", type="primary"):
                with st.spinner("Analizando con Gemini..."):
                    summary = gemini_analyzer.generate_executive_summary(df)
                    st.markdown(summary)

        elif analysis_type == "Activo Específico":
            selected_asset = st.selectbox(
                "Selecciona un activo",
                df['id_activo'].tolist()
            )

            if st.button("🔍 Analizar Activo", type="primary"):
                asset_data = df[df['id_activo'] == selected_asset].iloc[0]
                with st.spinner("Analizando con Gemini..."):
                    analysis = gemini_analyzer.analyze_asset(asset_data)
                    st.markdown(analysis)

        else:  # Pregunta Personalizada
            question = st.text_area(
                "Escribe tu pregunta sobre la flota",
                placeholder="Ej: ¿Qué mixers deberíamos reemplazar este año y por qué?"
            )

            if st.button("💬 Consultar a Gemini", type="primary") and question:
                with st.spinner("Consultando..."):
                    answer = gemini_analyzer.custom_query(df, question)
                    st.markdown(answer)

except Exception as e:
    st.error(f"❌ Error al cargar datos: {str(e)}")
    st.info("**Posibles causas:**")
    st.write("1. Verifica que las credenciales en 'Secrets' estén correctas")
    st.write("2. Verifica que el Google Sheet esté compartido con la service account")
    st.write("3. Verifica que las hojas se llamen exactamente: 'Activos', 'Mantenimiento', 'Costos_Referencia'")
    st.write("4. Verifica que Google Sheets API y Google Drive API estén habilitadas")

# Footer
st.markdown("---")
st.caption("Concremag S.A. - Sistema de Gestión de Activos | Powered by Gemini AI")
