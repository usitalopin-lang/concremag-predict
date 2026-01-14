import google.generativeai as genai
import pandas as pd

class GeminiAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def _ensure_costs(self, df):
        """Asegura que exista la columna de costo total"""
        if 'costo_mantenimiento' not in df.columns:
            if 'costo_repuestos' in df.columns and 'costo_mano_obra' in df.columns:
                df['costo_mantenimiento'] = df['costo_repuestos'] + df['costo_mano_obra']
            else:
                df['costo_mantenimiento'] = 0
        return df

    def generate_executive_summary(self, activos_df, mantenimiento_df, costos_df):
        mantenimiento_df = self._ensure_costs(mantenimiento_df.copy())
        
        critical_assets = activos_df[activos_df['health_score'] < 40]
        avg_health = activos_df['health_score'].mean()
        
        total_mant_cost = mantenimiento_df['costo_mantenimiento'].sum() if not mantenimiento_df.empty else 0
        total_mant_events = len(mantenimiento_df)

        prompt = f"""
Eres un consultor experto en gestión de activos industriales. Genera un resumen ejecutivo profesional basado en estos datos:

**FLOTA:**
- Total de activos: {len(activos_df)}
- Activos críticos (Health Score < 40): {len(critical_assets)}
- Health Score promedio: {avg_health:.1f}%

**MANTENIMIENTO:**
- Total de intervenciones: {total_mant_events}
- Costo total acumulado: ${total_mant_cost:,.0f} CLP

**ACTIVOS CRÍTICOS:**
{critical_assets[['id_activo', 'tipo_equipo', 'health_score', 'accion']].to_string() if not critical_assets.empty else 'No hay activos críticos'}

**HISTORIAL RECIENTE:**
{mantenimiento_df[['fecha', 'id_activo', 'tipo_mantenimiento', 'costo_mantenimiento']].tail(10).to_string(index=False) if not mantenimiento_df.empty else 'Sin datos'}

Genera un resumen de 200 palabras enfocándote en gastos y riesgos.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def analyze_asset(self, asset_data, mantenimiento_df, costos_df):
        mantenimiento_df = self._ensure_costs(mantenimiento_df.copy())
        
        asset_mant = mantenimiento_df[mantenimiento_df['id_activo'] == asset_data['id_activo']]
        
        total_mant_cost = asset_mant['costo_mantenimiento'].sum() if not asset_mant.empty else 0
        preventivos = len(asset_mant[asset_mant['tipo_mantenimiento'] == 'Preventivo'])
        correctivos = len(asset_mant[asset_mant['tipo_mantenimiento'] == 'Correctivo'])

        prompt = f"""
Analiza este activo:
ID: {asset_data['id_activo']} ({asset_data['tipo_equipo']})
Health Score: {asset_data['health_score']:.1f}%
Acción: {asset_data['accion']}

**MANTENIMIENTO:**
- Total eventos: {len(asset_mant)}
- Preventivos: {preventivos} | Correctivos: {correctivos}
- Gasto Total: ${total_mant_cost:,.0f} CLP

**DETALLE:**
{asset_mant[['fecha', 'descripcion', 'costo_mantenimiento']].tail(5).to_string(index=False) if not asset_mant.empty else 'Sin historial'}

Diagnostica el estado y justifica el gasto realizado.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def custom_query(self, activos_df, mantenimiento_df, costos_df, question):
        # 1. Preparar datos y asegurar costos
        mantenimiento_df = self._ensure_costs(mantenimiento_df.copy())
        
        # 2. CALCULAR TOTALES ROBUSTOS (ANUAL Y MENSUAL)
        resumen_calculado = "No hay datos suficientes para cálculos."
        
        if 'fecha' in mantenimiento_df.columns and not mantenimiento_df.empty:
            try:
                # A. Totales por Año
                gastos_anuales = mantenimiento_df.groupby(mantenimiento_df['fecha'].dt.year)['costo_mantenimiento'].sum()
                txt_anual = "\n".join([f"- Año {anio}: ${monto:,.0f} CLP" for anio, monto in gastos_anuales.items()])
                
                # B. Totales por Mes (Formato YYYY-MM)
                # Creamos columna temporal periodo
                mantenimiento_df['periodo'] = mantenimiento_df['fecha'].dt.to_period('M')
                gastos_mensuales = mantenimiento_df.groupby('periodo')['costo_mantenimiento'].sum()
                # Tomamos los últimos 24 meses para no saturar, o todos si son pocos
                txt_mensual = "\n".join([f"- {periodo}: ${monto:,.0f} CLP" for periodo, monto in gastos_mensuales.items()])
                
                resumen_calculado = f"""
                **TOTALES ANUALES (USAR ESTO PARA PREGUNTAS GENERALES):**
                {txt_anual}
                
                **TOTALES MENSUALES (USAR ESTO PARA DETALLES DE FECHAS):**
                {txt_mensual}
                """
            except Exception as e:
                resumen_calculado = f"Error calculando totales: {str(e)}"

        # 3. Preparar contexto de filas (Detalle individual)
        # Limitamos a las ultimas 50 transacciones para no romper el límite de tokens si hay muchos datos
        cols_mant = ['fecha', 'id_activo', 'tipo_mantenimiento', 'descripcion', 'costo_repuestos', 'costo_mano_obra', 'costo_mantenimiento']
        cols_final = [c for c in cols_mant if c in mantenimiento_df.columns]
        
        # Ordenamos por fecha descendente para que vea lo más reciente primero
        df_sorted = mantenimiento_df.sort_values('fecha', ascending=False).head(50)
        mant_context = df_sorted[cols_final].to_string(index=False) if not df_sorted.empty else 'Sin datos'

        prompt = f"""
Eres un asistente analítico de datos preciso para Concremag S.A.

**DATOS PRE-CALCULADOS (VERDAD ABSOLUTA MATEMÁTICA):**
{resumen_calculado}

**DETALLE DE LOS ÚLTIMOS REGISTROS (Para contexto de qué se reparó):**
{mant_context}

**PREGUNTA DEL USUARIO:**
{question}

INSTRUCCIONES CLAVE:
1. Prioridad TOTAL a la sección "DATOS PRE-CALCULADOS". Si te preguntan "¿Cuánto se gastó en septiembre 2025?", busca "2025-09" en la lista mensual y da ese valor exacto. NO intentes sumar filas manualmente.
2. Si te preguntan por un año, usa el total anual pre-calculado.
3. Si la pregunta es sobre el *detalle* (ej: "¿Qué se rompió?"), usa la tabla de detalle.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
