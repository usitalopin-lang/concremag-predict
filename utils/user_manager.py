"""
Gestor de usuarios autorizados - Lee desde Google Sheets
"""
import streamlit as st

class UserManager:
    def __init__(self, connector):
        """
        Inicializa el gestor de usuarios
        connector: instancia de SheetsConnector
        """
        self.connector = connector
        self.authorized_users = {}
        self.load_users()
    
    def load_users(self):
        """Carga usuarios desde Google Sheets"""
        try:
            users_data = self.connector.get_sheet_data('Usuarios')
            
            permissions_map = {
                'admin': ['view', 'edit', 'delete', 'manage_users'],
                'manager': ['view', 'edit'],
                'viewer': ['view']
            }
            
            for row in users_data:
                email = row.get('email', '').strip().lower()
                if email:
                    role = row.get('role', 'viewer').strip().lower()
                    self.authorized_users[email] = {
                        'name': row.get('name', '').strip(),
                        'role': role,
                        'company': row.get('company', 'Concremag S.A.').strip(),
                        'permissions': permissions_map.get(role, ['view'])
                    }
        except Exception as e:
            # Fallback: usuario por defecto si falla la carga
            st.warning(f"⚠️ No se pudo cargar usuarios desde Google Sheets. Usando usuario por defecto.")
            self.authorized_users = {
                'cf.lopezgaete@gmail.com': {
                    'name': 'Cristopher Lopez',
                    'role': 'admin',
                    'company': 'Concremag S.A.',
                    'permissions': ['view', 'edit', 'delete', 'manage_users']
                }
            }
    
    def is_authorized(self, email):
        """Verifica si el email está autorizado"""
        return email.lower().strip() in self.authorized_users
    
    def get_user_info(self, email):
        """Obtiene información del usuario"""
        return self.authorized_users.get(email.lower().strip(), None)
    
    def get_role(self, email):
        """Obtiene el rol del usuario"""
        user = self.get_user_info(email)
        return user['role'] if user else None
    
    def has_permission(self, email, permission):
        """Verifica si el usuario tiene un permiso específico"""
        user = self.get_user_info(email)
        if not user:
            return False
        return permission in user['permissions']
    
    def list_users(self):
        """Lista todos los usuarios autorizados"""
        return self.authorized_users
    
    def reload_users(self):
        """Recarga usuarios desde Google Sheets"""
        self.authorized_users = {}
        self.load_users()
