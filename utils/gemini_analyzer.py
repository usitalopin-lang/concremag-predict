import google.generativeai as genai
import pandas as pd

class GeminiAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_executive_summary(self, activos_df, mantenimiento_df, costos_df):
        """
        Genera resumen ejecutivo con datos de las 3 hojas
        """
        critical_assets = activos_df[activos_df['health_score'] < 40]
        avg_health = activos_df['health_score'].mean()
        
        # Calcular métricas de mantenimiento
        total_mant_cost = mantenimiento_df['costo_mantenimiento'].sum() if not mantenimiento_df.empty else 0
        total_mant_events = len(mantenimiento_df)

        prompt = f"""
Eres un consultor experto en gestión de activos industriales. Genera un resumen ejecutivo profesional basado en estos datos:

**FLOTA:**
- Total de activos: {len(activos_df)}
- Activos críticos (Health Score < 40): {len(critical_assets)}
- Health Score promedio de la flota: {avg_health:.1f}%
- Tipos de equipos: {activos_df['tipo_equipo'].unique().tolist()}

**MANTENIMIENTO:**
- Total de intervenciones registradas: {total_mant_events}
- Costo total de mantenimiento: ${total_mant_cost:,.0f} CLP

**ACTIVOS CRÍTICOS:**
{critical_assets[['id_activo', 'tipo_equipo', 'health_score', 'accion']].to_string() if not critical_assets.empty else 'No hay activos críticos'}

**HISTORIAL DE MANTENIMIENTO (últimos registros):**
{mantenimiento_df.tail(10).to_string(index=False) if not mantenimiento_df.empty else 'Sin datos de mantenimiento'}

Genera un resumen ejecutivo de 200-300 palabras con:
1. Estado general de la flota
2. Riesgos principales
3. Recomendaciones prioritarias
4. Impacto económico estimado
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al generar resumen: {str(e)}"

    def analyze_asset(self, asset_data, mantenimiento_df, costos_df):
        """
        Analiza un activo específico con su historial de mantenimiento
        """
        # Filtrar mantenimientos del activo
        asset_mant = mantenimiento_df[mantenimiento_df['id_activo'] == asset_data['id_activo']]
        
        # Calcular métricas de mantenimiento
        total_mant_cost = asset_mant['costo_mantenimiento'].sum() if not asset_mant.empty else 0
        num_preventivos = len(asset_mant[asset_mant['tipo_mantenimiento'] == 'Preventivo']) if not asset_mant.empty else 0
        num_correctivos = len(asset_mant[asset_mant['tipo_mantenimiento'] == 'Correctivo']) if not asset_mant.empty else 0

        prompt = f"""
Analiza este activo industrial y genera un informe técnico:

**DATOS DEL ACTIVO:**
- ID: {asset_data['id_activo']}
- Tipo: {asset_data['tipo_equipo']}
- Marca/Modelo: {asset_data['marca']} {asset_data['modelo']}
- Edad: {asset_data['edad_anos']} años
- Health Score: {asset_data['health_score']:.1f}%
- Horómetro: {asset_data['horometro_actual']:,.0f} hrs
- RUL: {asset_data['rul_horas']:,.0f} hrs
- Acción recomendada: {asset_data['accion']}

**HISTORIAL DE MANTENIMIENTO:**
- Total de mantenimientos: {len(asset_mant)}
- Preventivos: {num_preventivos}
- Correctivos: {num_correctivos}
- Costo total de mantenimiento: ${total_mant_cost:,.0f} CLP

**ÚLTIMOS MANTENIMIENTOS:**
{asset_mant.tail(5).to_string(index=False) if not asset_mant.empty else 'Sin historial de mantenimiento'}

Genera un análisis de 150-200 palabras con:
1. Diagnóstico del estado actual
2. Factores de riesgo basados en el historial
3. Recomendación técnica específica
4. Proyección de costos futuros
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al analizar activo: {str(e)}"

    def custom_query(self, activos_df, mantenimiento_df, costos_df, question):
        """
        Responde preguntas personalizadas con acceso a todas las hojas
        NOTA: activos_df debe ser el DataFrame CON métricas calculadas (df)
        """
        # Preparar contexto completo con todas las columnas relevantes
        # Verificar qué columnas existen para evitar errores
        columnas_disponibles = ['id_activo', 'tipo_equipo', 'marca', 'modelo', 'edad_anos']
        
        # Agregar columnas calculadas si existen
        if 'health_score' in activos_df.columns:
            columnas_disponibles.append('health_score')
        if 'accion' in activos_df.columns:
            columnas_disponibles.append('accion')
        if 'horizonte_meses' in activos_df.columns:
            columnas_disponibles.append('horizonte_meses')
        
        activos_context = activos_df[columnas_disponibles].to_string()
        
        prompt = f"""
Eres un experto en gestión de maquinaria pesada para construcción y hormigón.

**DATOS DE LA FLOTA:**
{activos_context}

**HISTORIAL DE MANTENIMIENTO:**
{mantenimiento_df.to_string(index=False) if not mantenimiento_df.empty else 'Sin datos de mantenimiento'}

**COSTOS DE REFERENCIA:**
{costos_df.to_string(index=False) if not costos_df.empty else 'Sin datos de costos'}

**PREGUNTA DEL USUARIO:**
{question}

**INSTRUCCIONES:**
- Responde de forma profesional, concisa y con recomendaciones accionables
- Si la pregunta requiere cálculos (ej: "cuántos mantenimientos"), usa los datos del historial
- Si la pregunta es sobre costos, suma los valores correspondientes
- Si no hay suficientes datos, indícalo claramente
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al procesar consulta: {str(e)}"
