import pandas as pd
import numpy as np
from datetime import datetime

class LifecycleCalculator:
    
    def calcular_health_score(self, row, df_mantenimiento, df_costos_ref):
        id_activo = row['id_activo']
        tipo_equipo = row['tipo_equipo']

        # 1. OBTENER REFERENCIAS
        ref = df_costos_ref[df_costos_ref['tipo_equipo'] == tipo_equipo]
        if ref.empty:
            vida_util_esperada = 15000
            tasa_depreciacion = 0.15
        else:
            vida_util_esperada = ref['vida_util_esperada_horas'].values[0]
            tasa_depreciacion = ref['tasa_depreciacion_anual'].values[0]

        # ---------------------------------------------------------
        # METRICA 1: DESGASTE FÍSICO (Horómetro) - PESO 30%
        # ---------------------------------------------------------
        # Usamos una curva cuadrática: el desgaste se acelera al final
        uso_pct = min(row['horometro_actual'] / vida_util_esperada, 1.5)
        score_uso = max(0, 100 * (1 - (uso_pct ** 1.2))) # Elevado a 1.2 para penalizar más el uso alto

        # ---------------------------------------------------------
        # METRICA 2: CONFIABILIDAD (Correctivo vs Preventivo) - PESO 40%
        # ---------------------------------------------------------
        mant_activo = df_mantenimiento[df_mantenimiento['id_activo'] == id_activo].copy()
        
        score_confiabilidad = 100
        penalizacion_correctiva = 0

        if not mant_activo.empty:
            # Asegurar que existan las columnas de costo
            if 'costo_mantenimiento' not in mant_activo.columns:
                 if 'costo_repuestos' in mant_activo.columns:
                     mant_activo['costo_mantenimiento'] = mant_activo['costo_repuestos'] + mant_activo['costo_mano_obra']
            
            # Filtrar solo mantenimientos del último año (o recientes)
            # Para simplificar este MVP, usamos todo el historial pero pesamos por tipo
            total_eventos = len(mant_activo)
            eventos_correctivos = len(mant_activo[mant_activo['tipo_mantenimiento'] == 'Correctivo'])
            
            if total_eventos > 0:
                tasa_fallas = eventos_correctivos / total_eventos
                # Si el 50% de tus entradas al taller son fallas, tu score baja a 50
                score_confiabilidad = max(0, 100 - (tasa_fallas * 100))
                
                # Penalización extra si hubo correctivos muy costosos recientemente
                gasto_total = mant_activo['costo_mantenimiento'].sum()
                gasto_correctivo = mant_activo[mant_activo['tipo_mantenimiento'] == 'Correctivo']['costo_mantenimiento'].sum()
                
                if gasto_total > 0 and (gasto_correctivo / gasto_total) > 0.6:
                    penalizacion_correctiva = 10 # Castigo extra de 10 puntos si gastas más en arreglar que en prevenir

        score_confiabilidad = max(0, score_confiabilidad - penalizacion_correctiva)

        # ---------------------------------------------------------
        # METRICA 3: EDAD Y OBSOLESCENCIA - PESO 30%
        # ---------------------------------------------------------
        edad = row['edad_anos']
        # Depreciación no lineal: Los primeros años valen más
        score_edad = max(0, 100 * np.exp(-0.1 * edad)) # Decaimiento exponencial suave

        # ---------------------------------------------------------
        # CALCULO FINAL
        # ---------------------------------------------------------
        # Ajustamos pesos: La Confiabilidad (historial real) pesa más que la teoría (edad)
        health_score = (score_uso * 0.30) + (score_edad * 0.20) + (score_confiabilidad * 0.50)

        # RUL (Remaining Useful Life) en horas
        rul_horas = max(0, vida_util_esperada - row['horometro_actual'])

        return health_score, rul_horas

    def calcular_metricas_completas(self, df_activos, df_mantenimiento, df_costos_ref):
        df = df_activos.copy()

        # Aplicar cálculo fila por fila
        resultados = df.apply(
            lambda row: self.calcular_health_score(row, df_mantenimiento, df_costos_ref),
            axis=1
        )
        
        # Desempaquetar resultados
        df['health_score'] = [x[0] for x in resultados]
        df['rul_horas'] = [x[1] for x in resultados]

        # Calcular costo último año de forma segura
        def get_costo_anual(id_act):
            filtro = df_mantenimiento[df_mantenimiento['id_activo'] == id_act]
            if filtro.empty: return 0
            if 'costo_mantenimiento' in filtro.columns:
                return filtro['costo_mantenimiento'].sum()
            elif 'costo_repuestos' in filtro.columns:
                return filtro['costo_repuestos'].sum() + filtro['costo_mano_obra'].sum()
            return 0

        df['costo_mantencion_ultimo_ano'] = df['id_activo'].apply(get_costo_anual)

        # Generar recomendaciones
        recomendaciones = df.apply(
            lambda row: self.recomendar_accion(row, df_costos_ref),
            axis=1
        )
        
        # Asignar columnas de recomendación
        col_names = ['accion', 'razon', 'detalle', 'horizonte_meses', 'prioridad', 'impacto_economico_clp']
        for i, col in enumerate(col_names):
            df[col] = [x[i] for x in recomendaciones]

        return df

    def recomendar_accion(self, row, df_costos_ref):
        health = row['health_score']
        rul = row['rul_horas']
        costo_mant = row.get('costo_mantencion_ultimo_ano', 0)
        valor_residual = row['valor_residual_estimado'] # Usamos valor residual, es más realista que valor compra

        # Umbrales ajustados para mayor sensibilidad
        if health < 40:
            accion = "🔴 REEMPLAZO CRÍTICO"
            razon = "Confiabilidad comprometida y vida útil excedida"
            detalle = f"Score ({health:.1f}%) bajo zona de seguridad. Alto riesgo de falla catastrófica."
            horizonte_meses = 3
            prioridad = 1
            impacto = valor_residual * 0.2 + costo_mant # Impacto alto

        elif health < 60:
            # Chequeo económico: ¿Estamos gastando más de lo que vale la máquina?
            if valor_residual > 0 and (costo_mant > valor_residual * 0.4):
                accion = "🟠 EVALUAR BAJA (ECONÓMICA)"
                razon = "Costo de mantenimiento supera el 40% del valor residual"
                detalle = f"Gasto anual ${costo_mant:,.0f} vs Valor Residual ${valor_residual:,.0f}. No es rentable reparar."
                horizonte_meses = 6
                prioridad = 1
                impacto = costo_mant
            else:
                accion = "🟡 OVERHAUL / REPARACIÓN MAYOR"
                razon = "Desgaste medio-alto. Requiere intervención para extender vida."
                detalle = f"RUL: {rul:.0f} hrs. Planificar reparación mayor."
                horizonte_meses = 6
                prioridad = 2
                impacto = costo_mant * 0.5

        elif health < 85:
            accion = "🟢 MANTENIMIENTO PREVENTIVO"
            razon = "Operación normal con desgaste esperado"
            detalle = "Reforzar pautas preventivas según horómetro."
            horizonte_meses = 12
            prioridad = 3
            impacto = 0

        else:
            accion = "✅ OPERACIÓN NORMAL"
            razon = "Equipo en óptimas condiciones"
            detalle = "Sin acciones correctivas requeridas."
            horizonte_meses = 24
            prioridad = 4
            impacto = 0

        return accion, razon, detalle, horizonte_meses, prioridad, impacto

    def priorizar_flota(self, df):
        # Ordenar por prioridad (ascendente) y health_score (ascendente)
        df_priorizado = df.sort_values(['prioridad', 'health_score']).copy()
        return df_priorizado[['id_activo', 'tipo_equipo', 'health_score', 'accion', 'razon', 
                              'detalle', 'horizonte_meses', 'prioridad', 'impacto_economico_clp']]
