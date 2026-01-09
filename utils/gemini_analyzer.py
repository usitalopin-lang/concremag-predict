import google.generativeai as genai
import pandas as pd

class GeminiAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # CORREGIDO: Usar gemini-2.0-flash-exp en lugar de gemini-1.5-flash
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_executive_summary(self, df):
        critical_assets = df[df['health_score'] < 40]
        avg_health = df['health_score'].mean()

        prompt = f"""
Eres un consultor experto en gestión de activos industriales. Genera un resumen ejecutivo profesional basado en estos datos:

- Total de activos: {len(df)}
- Activos críticos (Health Score < 40): {len(critical_assets)}
- Health Score promedio de la flota: {avg_health:.1f}%
- Tipos de equipos: {df['tipo_equipo'].unique().tolist()}

Datos críticos:
{critical_assets[['id_activo', 'tipo_equipo', 'health_score', 'accion']].to_string() if not critical_assets.empty else 'No hay activos críticos'}

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

    def analyze_asset(self, asset_data):
        prompt = f"""
Analiza este activo industrial y genera un informe técnico:

ID: {asset_data['id_activo']}
Tipo: {asset_data['tipo_equipo']}
Marca/Modelo: {asset_data['marca']} {asset_data['modelo']}
Edad: {asset_data['edad_anos']} años
Health Score: {asset_data['health_score']:.1f}%
Horómetro: {asset_data['horometro_actual']:,.0f} hrs
RUL: {asset_data['rul_horas']:,.0f} hrs
Acción recomendada: {asset_data['accion']}

Genera un análisis de 150-200 palabras con:
1. Diagnóstico del estado actual
2. Factores de riesgo
3. Recomendación técnica específica
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al analizar activo: {str(e)}"

    def custom_query(self, df, question):
        context = df[['id_activo', 'tipo_equipo', 'health_score', 'edad_anos', 'accion']].to_string()

        prompt = f"""
Eres un experto en gestión de maquinaria pesada para construcción y hormigón.

Datos de la flota:
{context}

Pregunta del usuario: {question}

Responde de forma profesional, concisa y con recomendaciones accionables.
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error al procesar consulta: {str(e)}"
