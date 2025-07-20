import os
from datetime import datetime

# Tokens y APIs
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'AQUI_VA_TU_TOKEN')
API_FOOTBALL_TOKEN = os.getenv('API_FOOTBALL_TOKEN', 'AQUI_TU_API_FOOTBALL_TOKEN')

# Configuración de ligas
LIGAS_PERMITIDAS = {
    128: 'Liga Argentina',
    13: 'Copa Libertadores',
    11: 'Copa Sudamericana',
    39: 'Premier League',
    140: 'La Liga de España',
    135: 'Serie A',
    78: 'Bundesliga',
    61: 'Ligue 1',
    88: 'Eredivisie',
    94: 'Primeira Liga'
}

# Límites del plan gratuito
LIMITES_GRATUITO = {
    'consultas_diarias': 10,
    'ligas_disponibles': [39, 140, 135, 78, 61],  # Solo ligas europeas
    'alertas_basicas': True,
    'resumen_diario': False,
    'estadisticas_avanzadas': False
}

# Funciones premium
FUNCIONES_PREMIUM = {
    'todas_las_ligas': True,
    'consultas_ilimitadas': True,
    'alertas_personalizadas': True,
    'resumen_semanal': True,
    'estadisticas_avanzadas': True,
    'historial_enfrentamientos': True,
    'predicciones': True,
    'sin_publicidad': True
}

# Precios (en USD)
PRECIOS = {
    'premium_mensual': 8.99,
    'premium_anual': 89.99,
    'pro_mensual': 14.99,
    'pro_anual': 149.99
}

# Configuración de monitoreo
MONITOREO_CONFIG = {
    'intervalo_segundos': 60,
    'horarios_activos': {
        'inicio': '08:00',
        'fin': '02:00'  # Hora argentina
    },
    'eventos_monitoreados': ['goles', 'tarjetas_rojas', 'finales', 'inicio_partido']
}

# Configuración de base de datos
DATABASE_CONFIG = {
    'file': 'users.db',
    'backup_interval': 24  # horas
}

# Mensajes del bot
MENSAJES = {
    'bienvenida_gratuito': (
        "¡Bienvenido al Bot de Fútbol Premium! ⚽️\n\n"
        "🔹 Plan Gratuito activo\n"
        "🔹 Ligas disponibles: Premier League, La Liga, Serie A, Bundesliga, Ligue 1\n"
        "🔹 10 consultas diarias\n"
        "🔹 Alertas básicas de goles\n\n"
        "💎 Actualiza a Premium para:\n"
        "• Todas las ligas (Argentina, Libertadores, etc.)\n"
        "• Consultas ilimitadas\n"
        "• Alertas personalizadas\n"
        "• Estadísticas avanzadas\n"
        "• Sin publicidad\n\n"
        "Desarrollado por Valentín Olivero"
    ),
    'bienvenida_premium': (
        "¡Bienvenido al Bot de Fútbol Premium! ⚽️\n\n"
        "💎 Plan Premium activo\n"
        "🔹 Todas las ligas disponibles\n"
        "🔹 Consultas ilimitadas\n"
        "🔹 Alertas personalizadas\n"
        "🔹 Estadísticas avanzadas\n"
        "🔹 Sin publicidad\n\n"
        "¡Disfruta de todas las funciones!\n\n"
        "Desarrollado por Valentín Olivero"
    ),
    'limite_alcanzado': (
        "⚠️ Has alcanzado el límite de consultas gratuitas.\n\n"
        "💎 Actualiza a Premium para consultas ilimitadas:\n"
        "• Todas las ligas\n"
        "• Estadísticas avanzadas\n"
        "• Alertas personalizadas\n"
        "• Sin publicidad\n\n"
        "Usa /premium para más información."
    )
}

# Configuración de administración
ADMIN_CONFIG = {
    'admin_ids': [],  # IDs de administradores
    'log_channel': None,  # Canal para logs
    'support_channel': None  # Canal de soporte
} 