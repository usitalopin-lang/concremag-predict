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
        # Asegurar costos antes de convertir a string
        mantenimiento_df = self._ensure_costs(mantenimiento_df.copy())
        
        # Seleccionar columnas clave para no saturar el prompt
        cols_mant = ['fecha', 'id_activo', 'tipo_mantenimiento', 'descripcion', 'costo_repuestos', 'costo_mano_obra', 'costo_mantenimiento']
        # Intersección para evitar error si falta alguna columna
        cols_final = [c for c in cols_mant if c in mantenimiento_df.columns]
        
        mant_context = mantenimiento_df[cols_final].to_string(index=False) if not mantenimiento_df.empty else 'Sin datos'

        prompt = f"""
Eres experto en gestión de flotas. Responde usando ESTRICTAMENTE los datos provistos.

**DATOS MANTENIMIENTO (Costos en CLP):**
{mant_context}

**PREGUNTA:**
{question}

Si preguntan por costos, suma los valores de la columna 'costo_mantenimiento' o 'costo_repuestos'/'costo_mano_obra'.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
