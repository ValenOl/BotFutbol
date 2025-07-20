import logging
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_CONFIG, MENSAJES
from database import db
import asyncio

class AdminPanel:
    def __init__(self):
        self.admin_ids = ADMIN_CONFIG['admin_ids']
        self.log_channel = ADMIN_CONFIG['log_channel']
        self.support_channel = ADMIN_CONFIG['support_channel']
    
    def is_admin(self, chat_id: int) -> bool:
        """Verifica si un usuario es administrador"""
        return chat_id in self.admin_ids
    
    async def admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú principal de administración"""
        if not self.is_admin(update.effective_chat.id):
            await update.message.reply_text("❌ No tienes permisos de administrador.")
            return
        
        keyboard = [
            [InlineKeyboardButton('📊 Estadísticas', callback_data='admin_stats')],
            [InlineKeyboardButton('👥 Gestión de Usuarios', callback_data='admin_users')],
            [InlineKeyboardButton('📢 Mensaje Masivo', callback_data='admin_broadcast')],
            [InlineKeyboardButton('💎 Gestión Premium', callback_data='admin_premium')],
            [InlineKeyboardButton('🔧 Configuración', callback_data='admin_config')],
            [InlineKeyboardButton('📋 Logs', callback_data='admin_logs')]
        ]
        
        mensaje = (
            "🔧 *Panel de Administración*\n\n"
            "Bienvenido al panel de control del bot.\n"
            "Selecciona una opción para continuar.\n\n"
            "Desarrollado por Valentín Olivero"
        )
        
        await update.message.reply_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los callbacks del panel de administración"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.message.chat_id):
            await query.edit_message_text("❌ No tienes permisos de administrador.")
            return
        
        data = query.data
        
        if data == 'admin_stats':
            await self.show_stats(query)
        elif data == 'admin_users':
            await self.show_users_menu(query)
        elif data == 'admin_broadcast':
            await self.show_broadcast_menu(query)
        elif data == 'admin_premium':
            await self.show_premium_menu(query)
        elif data == 'admin_config':
            await self.show_config_menu(query)
        elif data == 'admin_logs':
            await self.show_logs(query)
        elif data.startswith('admin_user_'):
            await self.show_user_details(query, data)
        elif data.startswith('admin_broadcast_'):
            await self.handle_broadcast(query, data)
    
    async def show_stats(self, query):
        """Muestra estadísticas del bot"""
        stats = db.get_stats()
        
        mensaje = (
            "📊 *Estadísticas del Bot*\n\n"
            f"👥 **Total de usuarios:** {stats.get('total_users', 0)}\n"
            f"💎 **Usuarios Premium:** {stats.get('premium_users', 0)}\n"
            f"📈 **% Premium:** {stats.get('premium_percentage', 0):.1f}%\n"
            f"🔍 **Consultas hoy:** {stats.get('queries_today', 0)}\n"
            f"⚡ **Usuarios activos hoy:** {stats.get('active_today', 0)}\n\n"
            f"📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_users_menu(self, query):
        """Menú de gestión de usuarios"""
        users = db.get_all_users()
        
        mensaje = (
            "👥 *Gestión de Usuarios*\n\n"
            f"Total de usuarios: {len(users)}\n\n"
            "Selecciona una opción:"
        )
        
        keyboard = [
            [InlineKeyboardButton('📋 Listar Usuarios', callback_data='admin_list_users')],
            [InlineKeyboardButton('🔍 Buscar Usuario', callback_data='admin_search_user')],
            [InlineKeyboardButton('📊 Usuarios Premium', callback_data='admin_premium_users')],
            [InlineKeyboardButton('📊 Usuarios Gratuitos', callback_data='admin_free_users')],
            [InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]
        ]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_broadcast_menu(self, query):
        """Menú de mensajes masivos"""
        mensaje = (
            "📢 *Mensaje Masivo*\n\n"
            "Envía un mensaje a todos los usuarios del bot.\n\n"
            "Selecciona el tipo de mensaje:"
        )
        
        keyboard = [
            [InlineKeyboardButton('📢 A Todos', callback_data='admin_broadcast_all')],
            [InlineKeyboardButton('💎 Solo Premium', callback_data='admin_broadcast_premium')],
            [InlineKeyboardButton('🔹 Solo Gratuitos', callback_data='admin_broadcast_free')],
            [InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]
        ]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_premium_menu(self, query):
        """Menú de gestión premium"""
        stats = db.get_stats()
        premium_users = stats.get('premium_users', 0)
        total_users = stats.get('total_users', 0)
        
        mensaje = (
            "💎 *Gestión Premium*\n\n"
            f"Usuarios Premium: {premium_users}/{total_users}\n"
            f"Porcentaje: {stats.get('premium_percentage', 0):.1f}%\n\n"
            "Selecciona una acción:"
        )
        
        keyboard = [
            [InlineKeyboardButton('➕ Dar Premium', callback_data='admin_give_premium')],
            [InlineKeyboardButton('➖ Quitar Premium', callback_data='admin_remove_premium')],
            [InlineKeyboardButton('📊 Estadísticas Premium', callback_data='admin_premium_stats')],
            [InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]
        ]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_config_menu(self, query):
        """Menú de configuración"""
        mensaje = (
            "🔧 *Configuración del Bot*\n\n"
            "Configuración actual:\n"
            "• Límite gratuito: 10 consultas/día\n"
            "• Monitoreo: 60 segundos\n"
            "• Ligas disponibles: 10\n\n"
            "Selecciona una opción:"
        )
        
        keyboard = [
            [InlineKeyboardButton('⚙️ Cambiar Límites', callback_data='admin_change_limits')],
            [InlineKeyboardButton('🕐 Cambiar Monitoreo', callback_data='admin_change_monitoring')],
            [InlineKeyboardButton('🏆 Gestionar Ligas', callback_data='admin_manage_leagues')],
            [InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]
        ]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_logs(self, query):
        """Muestra logs del sistema"""
        mensaje = (
            "📋 *Logs del Sistema*\n\n"
            "Funcionalidad en desarrollo.\n\n"
            "Los logs se guardan automáticamente en:\n"
            "• Errores de API\n"
            "• Actividad de usuarios\n"
            "• Cambios de suscripción\n"
            "• Mensajes masivos"
        )
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='admin_back')]]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_broadcast(self, query, data):
        """Maneja el envío de mensajes masivos"""
        broadcast_type = data.split('_')[2]
        
        # Guardar el tipo de broadcast en el contexto
        query.message.chat_data['broadcast_type'] = broadcast_type
        
        mensaje = (
            "📢 *Mensaje Masivo*\n\n"
            f"Tipo: {broadcast_type.upper()}\n\n"
            "Escribe el mensaje que quieres enviar:\n"
            "Usa /cancel para cancelar"
        )
        
        keyboard = [[InlineKeyboardButton('❌ Cancelar', callback_data='admin_back')]]
        
        await query.edit_message_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def send_broadcast(self, message_text: str, broadcast_type: str, context: ContextTypes.DEFAULT_TYPE) -> Dict:
        """Envía un mensaje masivo"""
        users = db.get_all_users()
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                # Filtrar usuarios según el tipo de broadcast
                if broadcast_type == 'premium' and not db.is_premium(user['chat_id']):
                    continue
                elif broadcast_type == 'free' and db.is_premium(user['chat_id']):
                    continue
                
                await context.bot.send_message(
                    chat_id=user['chat_id'],
                    text=message_text
                )
                sent_count += 1
                
                # Pequeña pausa para evitar límites de rate
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error sending broadcast to {user['chat_id']}: {e}")
                failed_count += 1
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(users)
        }
    
    async def log_admin_action(self, admin_id: int, action: str, details: str = "", context: ContextTypes.DEFAULT_TYPE = None):
        """Registra acciones de administración"""
        log_message = (
            f"🔧 **Acción de Administración**\n\n"
            f"👤 Admin ID: `{admin_id}`\n"
            f"🔧 Acción: {action}\n"
            f"📝 Detalles: {details}\n"
            f"🕐 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        if self.log_channel and context:
            try:
                await context.bot.send_message(
                    chat_id=self.log_channel,
                    text=log_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logging.error(f"Error sending admin log: {e}")
    
    def get_user_usage_stats(self, chat_id: int) -> Dict:
        """Obtiene estadísticas de uso de un usuario específico"""
        try:
            today = datetime.now().date()
            daily_queries = db.get_daily_queries_count(chat_id, today)
            user = db.get_user(chat_id)
            
            return {
                'chat_id': chat_id,
                'username': user.get('username', 'N/A'),
                'first_name': user.get('first_name', 'N/A'),
                'plan': user.get('plan', 'gratuito'),
                'daily_queries': daily_queries,
                'is_premium': db.is_premium(chat_id),
                'created_at': user.get('created_at', 'N/A'),
                'last_activity': user.get('last_activity', 'N/A')
            }
        except Exception as e:
            logging.error(f"Error getting user usage stats: {e}")
            return {}

# Instancia global del panel de administración
admin_panel = AdminPanel() 