import pandas as pd
import numpy as np
from datetime import datetime

class LifecycleCalculator:
    def calcular_health_score(self, row, df_mantenimiento, df_costos_ref):
        id_activo = row['id_activo']
        tipo_equipo = row['tipo_equipo']

        ref = df_costos_ref[df_costos_ref['tipo_equipo'] == tipo_equipo]
        if ref.empty:
            vida_util_esperada = 15000
            tasa_depreciacion = 0.15
        else:
            vida_util_esperada = ref['vida_util_esperada_horas'].values[0]
            tasa_depreciacion = ref['tasa_depreciacion_anual'].values[0]

        uso_pct = min(row['horometro_actual'] / vida_util_esperada, 1.2)
        score_uso = max(0, 100 - (uso_pct * 100))

        edad = row['edad_anos']
        score_edad = max(0, 100 - (edad * 10))

        mant_activo = df_mantenimiento[df_mantenimiento['id_activo'] == id_activo]
        if not mant_activo.empty:
            costo_total_mant = mant_activo['costo_repuestos'].sum() + mant_activo['costo_mano_obra'].sum()
            ratio_mant = min(costo_total_mant / row['valor_compra'], 1.0) if row['valor_compra'] > 0 else 0
            score_mant = max(0, 100 - (ratio_mant * 100))
        else:
            score_mant = 80

        health_score = (score_uso * 0.4) + (score_edad * 0.3) + (score_mant * 0.3)

        rul_horas = max(0, vida_util_esperada - row['horometro_actual'])

        return health_score, rul_horas

    def calcular_metricas_completas(self, df_activos, df_mantenimiento, df_costos_ref):
        df = df_activos.copy()

        df[['health_score', 'rul_horas']] = df.apply(
            lambda row: pd.Series(self.calcular_health_score(row, df_mantenimiento, df_costos_ref)),
            axis=1
        )

        df['costo_mantencion_ultimo_ano'] = df['id_activo'].apply(
            lambda x: df_mantenimiento[df_mantenimiento['id_activo'] == x][
                ['costo_repuestos', 'costo_mano_obra']
            ].sum().sum()
        )

        df[['accion', 'razon', 'detalle', 'horizonte_meses', 'prioridad', 'impacto_economico_clp']] = df.apply(
            lambda row: pd.Series(self.recomendar_accion(row, df_costos_ref)),
            axis=1
        )

        return df

    def recomendar_accion(self, row, df_costos_ref):
        health = row['health_score']
        edad = row['edad_anos']
        rul = row['rul_horas']
        costo_mant = row.get('costo_mantencion_ultimo_ano', 0)
        valor_compra = row['valor_compra']
        valor_residual = row['valor_residual_estimado']

        ref = df_costos_ref[df_costos_ref['tipo_equipo'] == row['tipo_equipo']]
        if not ref.empty:
            costo_dia_parada = ref['costo_dia_parada'].values[0]
            vida_util_esperada = ref['vida_util_esperada_horas'].values[0]
        else:
            costo_dia_parada = 500000
            vida_util_esperada = 15000

        ratio_mant_valor = (costo_mant / valor_compra) if valor_compra > 0 else 0

        if health < 30:
            accion = "🔴 REEMPLAZO INMEDIATO"
            razon = "Vida útil agotada, alto riesgo operacional"
            detalle = f"Health Score crítico ({health:.1f}%). RUL: {rul:.0f} hrs. Costo mantención/valor: {ratio_mant_valor:.1%}"
            horizonte_meses = 1
            prioridad = 1
            impacto = costo_dia_parada * 30 + costo_mant

        elif health < 50 and ratio_mant_valor > 0.25:
            accion = "🟠 REEMPLAZO PROGRAMADO"
            razon = "Costos de mantención excesivos vs valor del activo"
            detalle = f"Ratio mantención/valor: {ratio_mant_valor:.1%}. Recomendado reemplazar en próximos 6 meses."
            horizonte_meses = 6
            prioridad = 2
            impacto = costo_mant * 2

        elif health < 60:
            accion = "🟡 OVERHAUL / MANTENIMIENTO MAYOR"
            razon = "Desgaste significativo, requiere intervención profunda"
            detalle = f"Health Score: {health:.1f}%. Edad: {edad} años. Considerar overhaul para extender vida útil."
            horizonte_meses = 3
            prioridad = 2
            impacto = valor_compra * 0.3

        elif health < 75:
            accion = "🟢 MANTENIMIENTO PREVENTIVO REFORZADO"
            razon = "Activo en rango aceptable, requiere monitoreo"
            detalle = f"Programar mantenimientos preventivos cada 500 hrs. Health Score: {health:.1f}%"
            horizonte_meses = 12
            prioridad = 3
            impacto = costo_dia_parada * 5

        else:
            accion = "✅ MANTENIMIENTO ESTÁNDAR"
            razon = "Activo en óptimas condiciones"
            detalle = f"Continuar con plan de mantenimiento regular. Health Score: {health:.1f}%"
            horizonte_meses = 24
            prioridad = 4
            impacto = 0

        return accion, razon, detalle, horizonte_meses, prioridad, impacto

    def priorizar_flota(self, df):
        df_priorizado = df.sort_values(['prioridad', 'health_score']).copy()
        return df_priorizado[['id_activo', 'tipo_equipo', 'health_score', 'accion', 'razon', 
                              'detalle', 'horizonte_meses', 'prioridad', 'impacto_economico_clp']]
