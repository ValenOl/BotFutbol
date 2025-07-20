import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

class Database:
    def __init__(self, db_file: str = 'users.db'):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con todas las tablas necesarias"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    plan TEXT DEFAULT 'gratuito',
                    plan_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de consultas diarias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    query_type TEXT,
                    league_id INTEGER,
                    query_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES users (chat_id)
                )
            ''')
            
            # Tabla de alertas personalizadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    alert_type TEXT,
                    team_id INTEGER,
                    league_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES users (chat_id)
                )
            ''')
            
            # Tabla de estadísticas de uso
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    date DATE DEFAULT CURRENT_DATE,
                    queries_count INTEGER DEFAULT 0,
                    alerts_received INTEGER DEFAULT 0,
                    FOREIGN KEY (chat_id) REFERENCES users (chat_id)
                )
            ''')
            
            # Tabla de pagos (para futuras integraciones)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    plan_type TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'USD',
                    payment_method TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES users (chat_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, chat_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Agrega un nuevo usuario a la base de datos"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (chat_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding user {chat_id}: {e}")
            return False
    
    def get_user(self, chat_id: int) -> Optional[Dict]:
        """Obtiene información de un usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, username, first_name, last_name, plan, plan_expires_at, 
                           created_at, last_activity, is_active
                    FROM users WHERE chat_id = ?
                ''', (chat_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'chat_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'plan': row[4],
                        'plan_expires_at': row[5],
                        'created_at': row[6],
                        'last_activity': row[7],
                        'is_active': bool(row[8])
                    }
                return None
        except Exception as e:
            logging.error(f"Error getting user {chat_id}: {e}")
            return None
    
    def update_user_activity(self, chat_id: int):
        """Actualiza la última actividad del usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                ''', (chat_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating user activity {chat_id}: {e}")
    
    def is_premium(self, chat_id: int) -> bool:
        """Verifica si un usuario tiene plan premium activo"""
        user = self.get_user(chat_id)
        if not user:
            return False
        
        if user['plan'] == 'gratuito':
            return False
        
        if user['plan_expires_at']:
            expires_at = datetime.fromisoformat(user['plan_expires_at'])
            if expires_at < datetime.now():
                # Plan expirado, cambiar a gratuito
                self.update_user_plan(chat_id, 'gratuito')
                return False
        
        return True
    
    def update_user_plan(self, chat_id: int, plan: str, expires_at: datetime = None):
        """Actualiza el plan de un usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET plan = ?, plan_expires_at = ?
                    WHERE chat_id = ?
                ''', (plan, expires_at.isoformat() if expires_at else None, chat_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Error updating user plan {chat_id}: {e}")
    
    def can_make_query(self, chat_id: int) -> bool:
        """Verifica si un usuario puede hacer una consulta (límites del plan gratuito)"""
        if self.is_premium(chat_id):
            return True
        
        # Verificar límite diario para usuarios gratuitos
        today = datetime.now().date()
        daily_queries = self.get_daily_queries_count(chat_id, today)
        return daily_queries < 10  # Límite del plan gratuito
    
    def log_query(self, chat_id: int, query_type: str, league_id: int = None):
        """Registra una consulta del usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO daily_queries (chat_id, query_type, league_id)
                    VALUES (?, ?, ?)
                ''', (chat_id, query_type, league_id))
                conn.commit()
        except Exception as e:
            logging.error(f"Error logging query {chat_id}: {e}")
    
    def get_daily_queries_count(self, chat_id: int, date: datetime.date) -> int:
        """Obtiene el número de consultas de un usuario en una fecha específica"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM daily_queries 
                    WHERE chat_id = ? AND query_date = ?
                ''', (chat_id, date.isoformat()))
                return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Error getting daily queries count {chat_id}: {e}")
            return 0
    
    def add_user_alert(self, chat_id: int, alert_type: str, team_id: int = None, league_id: int = None) -> bool:
        """Agrega una alerta personalizada para un usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_alerts (chat_id, alert_type, team_id, league_id)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, alert_type, team_id, league_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding user alert {chat_id}: {e}")
            return False
    
    def get_user_alerts(self, chat_id: int) -> List[Dict]:
        """Obtiene las alertas personalizadas de un usuario"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT alert_type, team_id, league_id FROM user_alerts
                    WHERE chat_id = ? AND is_active = 1
                ''', (chat_id,))
                return [
                    {
                        'alert_type': row[0],
                        'team_id': row[1],
                        'league_id': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting user alerts {chat_id}: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """Obtiene todos los usuarios activos"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT chat_id, username, first_name, plan, created_at, last_activity
                    FROM users WHERE is_active = 1
                    ORDER BY last_activity DESC
                ''')
                return [
                    {
                        'chat_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'plan': row[3],
                        'created_at': row[4],
                        'last_activity': row[5]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas generales del bot"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Total usuarios
                cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
                total_users = cursor.fetchone()[0]
                
                # Usuarios premium
                cursor.execute('SELECT COUNT(*) FROM users WHERE plan != "gratuito" AND is_active = 1')
                premium_users = cursor.fetchone()[0]
                
                # Consultas hoy
                today = datetime.now().date()
                cursor.execute('SELECT COUNT(*) FROM daily_queries WHERE query_date = ?', (today.isoformat(),))
                queries_today = cursor.fetchone()[0]
                
                # Usuarios activos hoy
                cursor.execute('''
                    SELECT COUNT(DISTINCT chat_id) FROM daily_queries 
                    WHERE query_date = ?
                ''', (today.isoformat(),))
                active_today = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'premium_users': premium_users,
                    'queries_today': queries_today,
                    'active_today': active_today,
                    'premium_percentage': (premium_users / total_users * 100) if total_users > 0 else 0
                }
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return {}
    
    def backup_database(self):
        """Crea un backup de la base de datos"""
        try:
            import shutil
            from datetime import datetime
            backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(self.db_file, backup_file)
            logging.info(f"Database backup created: {backup_file}")
        except Exception as e:
            logging.error(f"Error creating backup: {e}")

# Instancia global de la base de datos
db = Database() 