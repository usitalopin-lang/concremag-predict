import pandas as pd
from google.oauth2 import service_account
import gspread
from datetime import datetime

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
            import streamlit as st
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

            if worksheet_name == "Activos":
                numeric_cols = ['ano_compra', 'horometro_actual', 'valor_compra', 'valor_residual_estimado']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                current_year = datetime.now().year
                df['edad_anos'] = current_year - df['ano_compra']

            elif worksheet_name == "Mantenimiento":
                numeric_cols = ['costo_repuestos', 'costo_mano_obra', 'horas_parada']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

            elif worksheet_name == "Costos_Referencia":
                numeric_cols = ['costo_hora_operacion', 'costo_dia_parada', 
                               'vida_util_esperada_horas', 'tasa_depreciacion_anual']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

            return df

        except Exception as e:
            print(f"Error al leer hoja {worksheet_name}: {str(e)}")
            return pd.DataFrame()

    def update_data(self, df, worksheet_name):
        ws = self.sheet.worksheet(worksheet_name)
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())
