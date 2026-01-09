# 📘 Guía de Configuración - Concremag AI

## 🎯 Paso 1: Preparar Google Cloud

### 1.1 Crear Proyecto
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Clic en "Select a project" > "New Project"
3. Nombre: `concremag-predict`
4. Clic en "Create"

### 1.2 Habilitar APIs
1. En el menú lateral: APIs & Services > Library
2. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### 1.3 Crear Service Account
1. IAM & Admin > Service Accounts
2. "Create Service Account"
3. Nombre: `concremag-sheets-api`
4. Role: **Editor**
5. Clic en "Create Key" > JSON
6. Descarga el archivo JSON (¡guárdalo seguro!)

### 1.4 Copiar Email de Service Account
Ejemplo: `concremag-sheets-api@concremag-predict.iam.gserviceaccount.com`

---

## 📊 Paso 2: Configurar Google Sheets

### 2.1 Crear el Spreadsheet
1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea un nuevo spreadsheet
3. Nómbralo: `Concremag - Gestión de Activos`

### 2.2 Crear las 3 Hojas
Renombra las pestañas exactamente así:
- `Activos`
- `Mantenimiento`
- `Costos_Referencia`

### 2.3 Agregar Encabezados

**Hoja "Activos":**
```
id_activo | tipo_equipo | marca | modelo | ano_compra | horometro_actual | valor_compra | valor_residual_estimado
```

**Hoja "Mantenimiento":**
```
id_activo | fecha | tipo_mantenimiento | descripcion | costo_repuestos | costo_mano_obra | horas_parada
```

**Hoja "Costos_Referencia":**
```
tipo_equipo | costo_hora_operacion | costo_dia_parada | vida_util_esperada_horas | tasa_depreciacion_anual
```

### 2.4 Compartir con Service Account
1. Clic en "Share" (arriba derecha)
2. Pega el email de la service account
3. Rol: **Editor**
4. Desactiva "Notify people"
5. Clic en "Share"

### 2.5 Copiar ID del Sheet
De la URL: `https://docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit`

---

## 🤖 Paso 3: Obtener Gemini API Key

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Clic en "Create API Key"
3. Selecciona tu proyecto de Google Cloud
4. Copia la API Key

---

## 🚀 Paso 4: Desplegar en Streamlit Cloud

### 4.1 Subir a GitHub
1. Crea un repositorio público en GitHub
2. Sube todos los archivos del proyecto
3. Asegúrate de que `runtime.txt` esté incluido

### 4.2 Crear App en Streamlit
1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con GitHub
3. Clic en "New app"
4. Selecciona tu repositorio
5. Main file: `app.py`
6. Clic en "Advanced settings"

### 4.3 Configurar Secrets
Pega esto en la sección "Secrets":

```toml
GEMINI_API_KEY = "TU_API_KEY_AQUI"
GOOGLE_SHEET_ID = "TU_SHEET_ID_AQUI"

[gcp_service_account]
type = "service_account"
project_id = "TU_PROJECT_ID"
private_key_id = "TU_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_KEY_COMPLETA\n-----END PRIVATE KEY-----\n"
client_email = "TU_SERVICE_ACCOUNT_EMAIL"
client_id = "TU_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "TU_CERT_URL"
universe_domain = "googleapis.com"
```

**⚠️ IMPORTANTE:** El `private_key` debe estar en UNA SOLA LÍNEA con `\n` en lugar de saltos de línea reales.

### 4.4 Deploy
1. Clic en "Deploy"
2. Espera 2-3 minutos
3. ¡Listo! 🎉

---

## 🔧 Troubleshooting

### Error: "App is in the oven" infinito
- **Causa:** Python 3.12+ incompatible
- **Solución:** Verifica que `runtime.txt` tenga `python-3.11`

### Error: "404 models/gemini-1.5-flash not found"
- **Causa:** Modelo deprecado
- **Solución:** El código ya usa `gemini-2.0-flash-exp`

### Error: "Permission denied" en Google Sheets
- **Causa:** Sheet no compartido con service account
- **Solución:** Comparte el Sheet con el email de la service account

### Error: "background_gradient requires matplotlib"
- **Causa:** Falta librería
- **Solución:** Ya incluida en `requirements.txt`

---

## ✅ Checklist Final

- [ ] Google Cloud Project creado
- [ ] APIs habilitadas (Sheets + Drive)
- [ ] Service Account creada y JSON descargado
- [ ] Google Sheet creado con 3 hojas
- [ ] Sheet compartido con service account
- [ ] Gemini API Key obtenida
- [ ] Código subido a GitHub
- [ ] `runtime.txt` incluido
- [ ] Secrets configurados en Streamlit Cloud
- [ ] App desplegada y funcionando

---

¡Felicidades! Tu sistema está listo para usar. 🚀
