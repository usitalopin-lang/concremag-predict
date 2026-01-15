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

            # --- LIMPIEZA DE MONEDA ---
            def clean_clp(val):
                if isinstance(val, str):
                    val = val.replace('$', '').replace('.', '').replace(',', '.')
                    return val.strip()
                return val

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
            print(f"Error lectura {worksheet_name}: {e}")
            return pd.DataFrame()

    def add_row(self, worksheet_name, row_data):
        """
        Busca la primera fila disponible y escribe en ella, 
        respetando el formato existente.
        """
        try:
            ws = self.sheet.worksheet(worksheet_name)
            
            # 1. Traemos solo la columna A (IDs) para contar cuántas filas reales hay
            # col_values(1) se detiene en el último valor escrito, ignora formatos vacíos
            col_ids = ws.col_values(1)
            
            # 2. La siguiente fila disponible es el largo de la columna + 1
            next_row = len(col_ids) + 1
            
            # 3. Usamos 'update' en lugar de 'append_row'
            # Esto escribe DENTRO de la celda existente (respetando tus colores y dropdowns)
            # range_name ej: "A21"
            ws.update(range_name=f"A{next_row}", values=[row_data])
            
            return True
        except Exception as e:
            st.error(f"Error escribiendo en Sheets: {str(e)}")
            return False
