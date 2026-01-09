# 🏗️ Concremag S.A. - Sistema de Gestión de Activos AI

Sistema inteligente para gestión del ciclo de vida de maquinaria pesada con análisis predictivo y recomendaciones basadas en IA.

## 🚀 Características

- **Dashboard Ejecutivo**: Visualización del estado de la flota en tiempo real
- **Análisis Predictivo**: Cálculo de Health Score y RUL (Remaining Useful Life)
- **Recomendaciones Inteligentes**: Sistema de semáforo con impacto económico
- **IA Gemini**: Análisis y consultas en lenguaje natural
- **Integración Google Sheets**: Base de datos en la nube sin infraestructura

## 📊 Estructura de Datos

### Hoja "Activos"
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id_activo | Texto | Identificador único (ej: MX-01) |
| tipo_equipo | Texto | Camión Mixer, Excavadora, etc. |
| marca | Texto | Fabricante |
| modelo | Texto | Modelo específico |
| ano_compra | Número | Año de adquisición |
| horometro_actual | Número | Horas de operación |
| valor_compra | Número | Valor de compra en CLP |
| valor_residual_estimado | Número | Valor residual en CLP |

### Hoja "Mantenimiento"
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id_activo | Texto | Referencia al activo |
| fecha | Fecha | Fecha del mantenimiento |
| tipo_mantenimiento | Texto | Preventivo/Correctivo |
| descripcion | Texto | Detalle de la intervención |
| costo_repuestos | Número | Costo en CLP |
| costo_mano_obra | Número | Costo en CLP |
| horas_parada | Número | Tiempo fuera de servicio |

### Hoja "Costos_Referencia"
| Columna | Tipo | Descripción |
|---------|------|-------------|
| tipo_equipo | Texto | Tipo de maquinaria |
| costo_hora_operacion | Número | Costo operativo por hora |
| costo_dia_parada | Número | Pérdida por día sin operar |
| vida_util_esperada_horas | Número | Vida útil en horas |
| tasa_depreciacion_anual | Número | Tasa de depreciación (0-1) |

## 🔧 Instalación y Despliegue

### Opción 1: Streamlit Cloud (Recomendado)

1. **Sube el proyecto a GitHub**
2. **Crea una app en [share.streamlit.io](https://share.streamlit.io)**
3. **Configura Secrets** (Settings > Secrets):
   ```toml
   GEMINI_API_KEY = "tu-api-key"
   GOOGLE_SHEET_ID = "tu-sheet-id"

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "..."
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   universe_domain = "googleapis.com"
   ```

### Opción 2: Local

1. **Clona el repositorio**
2. **Instala dependencias**: `pip install -r requirements.txt`
3. **Configura `.streamlit/secrets.toml`** (usa `secrets.toml.example` como plantilla)
4. **Ejecuta**: `streamlit run app.py`

## 🔑 Configuración de Credenciales

### Google Cloud Service Account

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un proyecto nuevo
3. Habilita APIs: Google Sheets API y Google Drive API
4. Crea Service Account (IAM > Service Accounts)
5. Descarga el JSON de credenciales
6. Comparte tu Google Sheet con el email de la service account

### Gemini API Key

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una API Key
3. Cópiala a los Secrets

## 📈 Algoritmo de Health Score

```
Health Score = (Score_Uso × 0.4) + (Score_Edad × 0.3) + (Score_Mantenimiento × 0.3)

Donde:
- Score_Uso = 100 - (Horómetro_Actual / Vida_Útil_Esperada × 100)
- Score_Edad = 100 - (Edad_Años × 10)
- Score_Mantenimiento = 100 - (Costo_Mant_Total / Valor_Compra × 100)
```

## 🚨 Sistema de Recomendaciones

| Health Score | Acción | Prioridad | Horizonte |
|--------------|--------|-----------|-----------|
| < 30% | 🔴 Reemplazo Inmediato | 1 | 1 mes |
| 30-50% | 🟠 Reemplazo Programado | 2 | 6 meses |
| 50-60% | 🟡 Overhaul / Mant. Mayor | 2 | 3 meses |
| 60-75% | 🟢 Mant. Preventivo Reforzado | 3 | 12 meses |
| > 75% | ✅ Mantenimiento Estándar | 4 | 24 meses |

## 🤝 Soporte

Para consultas técnicas: [support@concremag.cl](mailto:support@concremag.cl)

## 📄 Licencia

Propiedad de Concremag S.A. - Todos los derechos reservados.
