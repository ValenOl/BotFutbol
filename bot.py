import logging
import os
import asyncio
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler
)
from telegram.error import BadRequest
from typing import List

# Importar módulos personalizados
from config import *
from database import db
from premium_features import premium
from admin_panel import admin_panel

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Estados para conversaciones
WAITING_BROADCAST_MESSAGE = 1

class BotFutbolPremium:
    def __init__(self):
        self.api_token = API_FOOTBALL_TOKEN
        self.headers = {'x-apisports-key': self.api_token}
        self.base_url = 'https://v3.football.api-sports.io'
        
        # Sets para evitar notificaciones duplicadas
        self.goles_notificados = set()
        self.finales_notificados = set()
        self.rojass_notificadas = set()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Menú principal"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Registrar usuario en la base de datos
        db.add_user(chat_id, user.username, user.first_name, user.last_name)
        db.update_user_activity(chat_id)
        
        # Determinar mensaje según el plan
        is_premium = db.is_premium(chat_id)
        mensaje = MENSAJES['bienvenida_premium'] if is_premium else MENSAJES['bienvenida_gratuito']
        
        # Crear teclado según el plan
        keyboard = self.create_main_keyboard(is_premium)
        
        await update.message.reply_text(
            mensaje,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    def create_main_keyboard(self, is_premium: bool) -> List[List[InlineKeyboardButton]]:
        """Crea el teclado principal según el plan del usuario"""
        keyboard = [
            [InlineKeyboardButton('📅 Partidos de hoy', callback_data='partidos')],
            [InlineKeyboardButton('🏆 Tabla de posiciones', callback_data='tabla')],
            [InlineKeyboardButton('🥅 Goleadores', callback_data='goleadores')],
        ]
        
        if is_premium:
            # Funciones premium
            keyboard.extend([
                [InlineKeyboardButton('📊 Estadísticas Avanzadas', callback_data='estadisticas_avanzadas')],
                [InlineKeyboardButton('📰 Resumen Semanal', callback_data='resumen_semanal')],
                [InlineKeyboardButton('🔍 Historial H2H', callback_data='h2h')],
                [InlineKeyboardButton('🔮 Predicciones', callback_data='predicciones')],
                [InlineKeyboardButton('⚙️ Alertas Personalizadas', callback_data='alertas_personalizadas')],
            ])
        else:
            # Funciones gratuitas limitadas
            keyboard.extend([
                [InlineKeyboardButton('📊 Estadísticas Básicas', callback_data='estadisticas_basicas')],
                [InlineKeyboardButton('💎 Actualizar a Premium', callback_data='premium_info')],
            ])
        
        keyboard.append([InlineKeyboardButton('ℹ️ Ayuda', callback_data='ayuda')])
        
        return keyboard
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todos los callbacks de botones"""
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        data = query.data
        
        # Actualizar actividad del usuario
        db.update_user_activity(chat_id)
        
        # Verificar límites para usuarios gratuitos
        if not db.is_premium(chat_id) and not db.can_make_query(chat_id):
            await query.edit_message_text(MENSAJES['limite_alcanzado'], parse_mode='Markdown')
            return
        
        # Manejar diferentes tipos de callbacks
        if data == 'partidos':
            await self.show_ligas_menu(query, 'partidos')
        elif data == 'tabla':
            await self.show_ligas_menu(query, 'tabla')
        elif data == 'goleadores':
            await self.show_ligas_menu(query, 'goleadores')
        elif data == 'estadisticas_avanzadas':
            if db.is_premium(chat_id):
                await self.show_ligas_menu(query, 'estadisticas_avanzadas')
            else:
                await self.show_premium_required(query)
        elif data == 'estadisticas_basicas':
            await self.show_ligas_menu(query, 'estadisticas_basicas')
        elif data == 'resumen_semanal':
            if db.is_premium(chat_id):
                await self.show_ligas_menu(query, 'resumen_semanal')
            else:
                await self.show_premium_required(query)
        elif data == 'h2h':
            if db.is_premium(chat_id):
                await self.show_h2h_menu(query)
            else:
                await self.show_premium_required(query)
        elif data == 'predicciones':
            if db.is_premium(chat_id):
                await self.show_ligas_menu(query, 'predicciones')
            else:
                await self.show_premium_required(query)
        elif data == 'alertas_personalizadas':
            if db.is_premium(chat_id):
                await self.show_alerts_menu(query)
            else:
                await self.show_premium_required(query)
        elif data == 'premium_info':
            await self.show_premium_info(query)
        elif data == 'ayuda':
            await self.show_help(query)
        elif data.startswith('liga_'):
            await self.handle_liga_callback(query, data)
        elif data.startswith('partido_'):
            await self.handle_partido_callback(query, data)
        elif data.startswith('admin_'):
            await admin_panel.admin_callback(update, context)
        elif data == 'back':
            await self.show_main_menu(query)
    
    async def show_ligas_menu(self, query, tipo: str):
        """Muestra menú de ligas disponibles según el plan"""
        chat_id = query.message.chat_id
        is_premium = db.is_premium(chat_id)
        
        if is_premium:
            # Todas las ligas para premium
            ligas_disponibles = LIGAS_PERMITIDAS
        else:
            # Solo ligas gratuitas
            ligas_disponibles = {k: v for k, v in LIGAS_PERMITIDAS.items() 
                               if k in LIMITES_GRATUITO['ligas_disponibles']}
        
        keyboard = [
            [InlineKeyboardButton(nombre, callback_data=f"liga_{tipo}_{lid}")]
            for lid, nombre in ligas_disponibles.items()
        ]
        keyboard.append([InlineKeyboardButton('🔙 Volver', callback_data='back')])
        
        mensaje = f"Selecciona una liga para {tipo.replace('_', ' ')}:"
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def handle_liga_callback(self, query, data: str):
        """Maneja callbacks de ligas específicas"""
        _, tipo, liga_id = data.split('_')
        liga_id = int(liga_id)
        chat_id = query.message.chat_id
        
        # Registrar consulta
        db.log_query(chat_id, tipo, liga_id)
        
        if tipo == 'partidos':
            await self.get_partidos_hoy(query, liga_id)
        elif tipo == 'tabla':
            await self.get_tabla_posiciones(query, liga_id)
        elif tipo == 'goleadores':
            await self.get_goleadores(query, liga_id)
        elif tipo == 'estadisticas_avanzadas':
            await self.get_estadisticas_avanzadas(query, liga_id)
        elif tipo == 'estadisticas_basicas':
            await self.get_estadisticas_basicas(query, liga_id)
        elif tipo == 'resumen_semanal':
            await self.get_resumen_semanal(query, liga_id)
        elif tipo == 'predicciones':
            await self.get_predicciones(query, liga_id)
    
    async def get_partidos_hoy(self, query, liga_id: int):
        """Obtiene partidos del día para una liga"""
        today = datetime.now().date()
        date_str = today.strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/fixtures"
        params = {
            'league': liga_id,
            'date': date_str,
            'season': datetime.now().year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            partidos = []
            
            if data['response']:
                for fixture in data['response']:
                    home = fixture['teams']['home']['name']
                    away = fixture['teams']['away']['name']
                    utc_time = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                    arg_time = utc_time - timedelta(hours=3)
                    hora = arg_time.strftime('%H:%M')
                    partidos.append(f"{hora} - {home} vs {away}")
                
                mensaje = f"📅 Partidos de hoy en {LIGAS_PERMITIDAS[liga_id]}:\n\n" + "\n".join(partidos)
            else:
                mensaje = f"No hay partidos programados para hoy en {LIGAS_PERMITIDAS[liga_id]}."
        else:
            mensaje = "No se pudo obtener la información de partidos."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_tabla_posiciones(self, query, liga_id: int):
        """Obtiene tabla de posiciones"""
        url = f"{self.base_url}/standings"
        params = {
            'league': liga_id,
            'season': datetime.now().year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            tabla = []
            
            if data['response']:
                league_data = data['response'][0]
                for team in league_data['league']['standings'][0]:
                    pos = team['rank']
                    nombre = team['team']['name']
                    pts = team['points']
                    pj = team['all']['played']
                    tabla.append(f"{pos}. {nombre} ({pts} pts, {pj} PJ)")
                
                mensaje = f"🏆 Tabla de posiciones - {LIGAS_PERMITIDAS[liga_id]}:\n\n" + "\n".join(tabla)
            else:
                mensaje = f"No se pudo obtener la tabla de {LIGAS_PERMITIDAS[liga_id]}."
        else:
            mensaje = "No se pudo obtener la tabla de posiciones."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_goleadores(self, query, liga_id: int):
        """Obtiene goleadores de una liga"""
        url = f"{self.base_url}/players/topscorers"
        params = {
            'league': liga_id,
            'season': datetime.now().year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            goleadores = []
            
            if data['response']:
                for player in data['response'][:10]:  # Top 10
                    nombre = player['player']['name']
                    equipo = player['statistics'][0]['team']['name']
                    goles = player['statistics'][0]['goals']['total']
                    goleadores.append(f"{nombre} ({equipo}) - {goles} goles")
                
                mensaje = f"🥅 Goleadores - {LIGAS_PERMITIDAS[liga_id]}:\n\n" + "\n".join(goleadores)
            else:
                mensaje = f"No se pudo obtener los goleadores de {LIGAS_PERMITIDAS[liga_id]}."
        else:
            mensaje = "No se pudo obtener la información de goleadores."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_estadisticas_avanzadas(self, query, liga_id: int):
        """Obtiene estadísticas avanzadas (solo premium)"""
        # Obtener partidos recientes para mostrar estadísticas
        today = datetime.now().date()
        date_str = today.strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/fixtures"
        params = {
            'league': liga_id,
            'date': date_str,
            'season': datetime.now().year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['response']:
                # Tomar el primer partido para estadísticas
                fixture_id = data['response'][0]['fixture']['id']
                stats = premium.get_advanced_stats(fixture_id)
                
                mensaje = f"📊 Estadísticas Avanzadas - {LIGAS_PERMITIDAS[liga_id]}:\n\n"
                
                for team, team_stats in stats.items():
                    mensaje += f"**{team}:**\n"
                    for stat_type, value in team_stats.items():
                        mensaje += f"• {stat_type}: {value}\n"
                    mensaje += "\n"
            else:
                mensaje = f"No hay partidos recientes en {LIGAS_PERMITIDAS[liga_id]} para mostrar estadísticas."
        else:
            mensaje = "No se pudo obtener las estadísticas avanzadas."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_estadisticas_basicas(self, query, liga_id: int):
        """Obtiene estadísticas básicas (plan gratuito)"""
        mensaje = (
            f"📊 Estadísticas Básicas - {LIGAS_PERMITIDAS[liga_id]}\n\n"
            "Estadísticas básicas disponibles en el plan gratuito.\n\n"
            "💎 Actualiza a Premium para:\n"
            "• Estadísticas detalladas por partido\n"
            "• Análisis de posesión\n"
            "• Tiros a puerta\n"
            "• Faltas y tarjetas\n"
            "• Y mucho más..."
        )
        
        keyboard = [
            [InlineKeyboardButton('💎 Actualizar a Premium', callback_data='premium_info')],
            [InlineKeyboardButton('🔙 Volver', callback_data='back')]
        ]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_resumen_semanal(self, query, liga_id: int):
        """Obtiene resumen semanal (solo premium)"""
        summary = premium.get_weekly_summary(liga_id)
        
        if summary:
            mensaje = (
                f"📰 Resumen Semanal - {summary['league_name']}\n\n"
                f"📅 Período: {summary['period']}\n"
                f"⚽ Partidos jugados: {summary['total_matches']}\n"
                f"🥅 Promedio de goles: {summary['goals_per_match']}\n\n"
            )
            
            if summary['biggest_wins']:
                mensaje += "🏆 Mayores victorias:\n"
                for win in summary['biggest_wins'][:3]:
                    mensaje += f"• {win['home_team']} {win['score']} {win['away_team']}\n"
        else:
            mensaje = f"No hay datos suficientes para generar el resumen semanal de {LIGAS_PERMITIDAS[liga_id]}."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def get_predicciones(self, query, liga_id: int):
        """Obtiene predicciones (solo premium)"""
        # Obtener partidos próximos
        today = datetime.now().date()
        date_str = today.strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/fixtures"
        params = {
            'league': liga_id,
            'date': date_str,
            'season': datetime.now().year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['response']:
                # Tomar el primer partido para predicción
                fixture_id = data['response'][0]['fixture']['id']
                prediction = premium.get_match_prediction(fixture_id)
                
                if prediction:
                    pred = prediction['prediction']
                    mensaje = (
                        f"🔮 Predicción - {prediction['home_team']} vs {prediction['away_team']}\n\n"
                        f"🏠 Victoria Local: {pred['home_win_probability']}%\n"
                        f"✈️ Victoria Visitante: {pred['away_win_probability']}%\n"
                        f"🤝 Empate: {pred['draw_probability']}%\n\n"
                        f"📊 Predicción: {pred['predicted_result']}\n"
                        f"🎯 Confianza: {pred['confidence']}"
                    )
                else:
                    mensaje = "No se pudo generar la predicción para este partido."
            else:
                mensaje = f"No hay partidos próximos en {LIGAS_PERMITIDAS[liga_id]} para predicciones."
        else:
            mensaje = "No se pudo obtener las predicciones."
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def show_premium_required(self, query):
        """Muestra mensaje cuando se requiere plan premium"""
        mensaje = (
            "💎 *Función Premium Requerida*\n\n"
            "Esta función está disponible solo para usuarios Premium.\n\n"
            "💎 Actualiza a Premium para acceder a:\n"
            "• Estadísticas avanzadas\n"
            "• Resúmenes semanales\n"
            "• Historial de enfrentamientos\n"
            "• Predicciones de partidos\n"
            "• Alertas personalizadas\n"
            "• Todas las ligas\n"
            "• Consultas ilimitadas\n"
            "• Sin publicidad\n\n"
            f"💵 Precio: ${PRECIOS['premium_mensual']}/mes"
        )
        
        keyboard = [
            [InlineKeyboardButton('💎 Actualizar a Premium', callback_data='premium_info')],
            [InlineKeyboardButton('🔙 Volver', callback_data='back')]
        ]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def show_premium_info(self, query):
        """Muestra información sobre planes premium"""
        mensaje = (
            "💎 *Planes Premium*\n\n"
            "**Plan Premium Mensual:**\n"
            f"💵 ${PRECIOS['premium_mensual']}/mes\n"
            "• Todas las ligas disponibles\n"
            "• Consultas ilimitadas\n"
            "• Estadísticas avanzadas\n"
            "• Resúmenes semanales\n"
            "• Historial H2H\n"
            "• Predicciones\n"
            "• Alertas personalizadas\n"
            "• Sin publicidad\n\n"
            "**Plan Premium Anual:**\n"
            f"💵 ${PRECIOS['premium_anual']}/año (2 meses gratis)\n\n"
            "**Plan Pro Mensual:**\n"
            f"💵 ${PRECIOS['pro_mensual']}/mes\n"
            "• Todo lo de Premium\n"
            "• Soporte prioritario\n"
            "• Funciones beta\n\n"
            "Para suscribirte, contacta al administrador:\n"
            "@tu_usuario_admin"
        )
        
        keyboard = [
            [InlineKeyboardButton('🔙 Volver', callback_data='back')]
        ]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def show_help(self, query):
        """Muestra ayuda del bot"""
        mensaje = (
            "ℹ️ *Ayuda del Bot*\n\n"
            "**Comandos disponibles:**\n"
            "/start - Menú principal\n"
            "/help - Esta ayuda\n"
            "/premium - Información premium\n"
            "/admin - Panel de administración (solo admins)\n\n"
            "**Funciones gratuitas:**\n"
            "• Partidos de hoy (ligas europeas)\n"
            "• Tabla de posiciones\n"
            "• Goleadores\n"
            "• Estadísticas básicas\n"
            "• 10 consultas diarias\n\n"
            "**Funciones Premium:**\n"
            "• Todas las ligas\n"
            "• Consultas ilimitadas\n"
            "• Estadísticas avanzadas\n"
            "• Resúmenes semanales\n"
            "• Historial H2H\n"
            "• Predicciones\n"
            "• Alertas personalizadas\n\n"
            "Desarrollado por Valentín Olivero"
        )
        
        keyboard = [[InlineKeyboardButton('🔙 Volver', callback_data='back')]]
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def show_main_menu(self, query):
        """Muestra el menú principal"""
        chat_id = query.message.chat_id
        is_premium = db.is_premium(chat_id)
        
        mensaje = MENSAJES['bienvenida_premium'] if is_premium else MENSAJES['bienvenida_gratuito']
        keyboard = self.create_main_keyboard(is_premium)
        
        try:
            await query.edit_message_text(
                mensaje,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    
    async def monitorear_eventos(self, application):
        """Monitorea eventos en vivo y envía alertas"""
        while True:
            try:
                # Obtener partidos en vivo
                url = f"{self.base_url}/fixtures"
                params = {'live': 'all'}
                response = requests.get(url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for fixture in data['response']:
                        league_id = fixture['league']['id']
                        if league_id not in LIGAS_PERMITIDAS:
                            continue
                        
                        fixture_id = fixture['fixture']['id']
                        league = LIGAS_PERMITIDAS[league_id]
                        home = fixture['teams']['home']['name']
                        away = fixture['teams']['away']['name']
                        goals_home = fixture['goals']['home']
                        goals_away = fixture['goals']['away']
                        status = fixture['fixture']['status']['short']
                        
                        # Verificar goles nuevos
                        if status == 'LIVE' and (goals_home > 0 or goals_away > 0):
                            key = (fixture_id, goals_home, goals_away)
                            if key not in self.goles_notificados:
                                self.goles_notificados.add(key)
                                
                                mensaje = (
                                    f"⚽️ ¡GOL EN VIVO! ⚽️\n"
                                    f"🏆 {league}\n"
                                    f"🔔 {home} {goals_home} - {goals_away} {away}\n"
                                    f"-----------------------------"
                                )
                                
                                await self.send_alert_to_users(mensaje, application)
                        
                        # Verificar final de partido
                        if status == 'FT' and fixture_id not in self.finales_notificados:
                            self.finales_notificados.add(fixture_id)
                            
                            utc_time = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                            arg_time = utc_time - timedelta(hours=3)
                            hora = arg_time.strftime('%H:%M')
                            
                            mensaje = (
                                f"🏁 FINAL DEL PARTIDO 🏁\n"
                                f"🏆 {league}\n"
                                f"{hora} - {home} {goals_home}-{goals_away} {away}\n"
                                f"-----------------------------"
                            )
                            
                            await self.send_alert_to_users(mensaje, application)
                
                await asyncio.sleep(60)  # Esperar 1 minuto
                
            except Exception as e:
                logging.error(f"Error en monitoreo de eventos: {e}")
                await asyncio.sleep(60)
    
    async def send_alert_to_users(self, mensaje: str, application):
        """Envía alerta a todos los usuarios activos"""
        users = db.get_all_users()
        
        for user in users:
            try:
                await application.bot.send_message(
                    chat_id=user['chat_id'],
                    text=mensaje
                )
                await asyncio.sleep(0.1)  # Pequeña pausa
            except Exception as e:
                logging.error(f"Error enviando alerta a {user['chat_id']}: {e}")

# Instancia global del bot
bot = BotFutbolPremium()

# Handlers
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await bot.start(update, context)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await bot.handle_callback(update, context)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_panel.admin_menu(update, context)

# Main
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Handlers principales
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('admin', admin_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # Handler para mensajes de texto (bienvenida automática)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_handler))
    
    print('Bot Premium iniciado. Esperando mensajes...')
    print('Desarrollado por Valentín Olivero')
    
    # Iniciar monitoreo de eventos
    asyncio.get_event_loop().create_task(bot.monitorear_eventos(app))
    
    # Ejecutar el bot
    app.run_polling() 