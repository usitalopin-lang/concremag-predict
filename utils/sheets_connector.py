import pandas as pd
from google.oauth2 import service_account
import gspread
from datetime import datetime
import streamlit as st

class SheetsConnector:
    def __init__(self, credentials_path=None, spreadsheet_id=None):
        self.spreadsheet_id = spreadsheet_id

        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        if credentials_path:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
        else:
            # Asume que está en st.secrets
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )

        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(spreadsheet_id)

    def get_data(self, worksheet_name):
        try:
            ws = self.sheet.worksheet(worksheet_name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)

            # --- FUNCIÓN DE LIMPIEZA DE MONEDA CHILENA ---
            def clean_clp(val):
                if isinstance(val, str):
                    val = val.replace('$', '').replace('.', '').replace(',', '.')
                    return val.strip()
                return val
            # ---------------------------------------------

            if worksheet_name == "Activos":
                numeric_cols = ['ano_compra', 'horometro_actual', 'valor_compra', 'valor_residual_estimado']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(clean_clp)
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                current_year = datetime.now().year
                if 'ano_compra' in df.columns:
                    df['edad_anos'] = current_year - df['ano_compra']

            elif worksheet_name == "Mantenimiento":
                numeric_cols = ['costo_repuestos', 'costo_mano_obra', 'horas_parada']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(clean_clp)
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                if 'costo_repuestos' in df.columns and 'costo_mano_obra' in df.columns:
                    df['costo_mantenimiento'] = df['costo_repuestos'] + df['costo_mano_obra']

                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

            elif worksheet_name == "Costos_Referencia":
                numeric_cols = ['costo_hora_operacion', 'costo_dia_parada', 
                               'vida_util_esperada_horas', 'tasa_depreciacion_anual']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(clean_clp)
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            return df

        except Exception as e:
            # Si falla, devolvemos un DataFrame vacío para no romper la app
            print(f"Error al leer hoja {worksheet_name}: {str(e)}")
            return pd.DataFrame()

    def add_row(self, worksheet_name, row_data):
        """
        Agrega una nueva fila al final de la hoja.
        row_data: Lista de valores [val1, val2, val3...]
        """
        try:
            ws = self.sheet.worksheet(worksheet_name)
            ws.append_row(row_data)
            return True
        except Exception as e:
            st.error(f"Error escribiendo en Sheets: {str(e)}")
            return False
