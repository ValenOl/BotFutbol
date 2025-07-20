# ⚽ Bot de Fútbol Premium

Bot de Telegram para seguimiento de fútbol en vivo con sistema de suscripciones premium y funciones avanzadas.

## 🚀 Características

### Plan Gratuito
- 📅 Partidos de hoy (ligas europeas)
- 🏆 Tabla de posiciones
- 🥅 Goleadores
- 📊 Estadísticas básicas
- 🔔 Alertas de goles en vivo
- ⚡ 10 consultas diarias

### Plan Premium
- 💎 Todas las ligas disponibles
- 🔍 Consultas ilimitadas
- 📊 Estadísticas avanzadas
- 📰 Resúmenes semanales
- 🔍 Historial de enfrentamientos (H2H)
- 🔮 Predicciones de partidos
- ⚙️ Alertas personalizadas
- 🚫 Sin publicidad

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd BotFutbol
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crear archivo `.env` en la raíz del proyecto:
```env
TELEGRAM_TOKEN=tu_token_de_telegram
API_FOOTBALL_TOKEN=tu_token_de_api_football
```

### 4. Configurar tokens

#### Telegram Bot Token
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot con `/newbot`
3. Copia el token y agrégalo a tu archivo `.env`

#### API-Football Token
1. Regístrate en [API-Football](https://www.api-football.com/)
2. Obtén tu token de la API
3. Agrégalo a tu archivo `.env`

### 5. Configurar administradores
Edita `config.py` y agrega los IDs de los administradores:
```python
ADMIN_CONFIG = {
    'admin_ids': [123456789, 987654321],  # IDs de administradores
    'log_channel': -1001234567890,  # Canal para logs (opcional)
    'support_channel': -1001234567890  # Canal de soporte (opcional)
}
```

## 🚀 Ejecución

```bash
python bot.py
```

## 📋 Comandos Disponibles

### Usuarios
- `/start` - Menú principal
- `/help` - Ayuda del bot
- `/premium` - Información sobre planes premium

### Administradores
- `/admin` - Panel de administración

## 🏆 Ligas Soportadas

### Plan Gratuito
- Premier League (Inglaterra)
- La Liga (España)
- Serie A (Italia)
- Bundesliga (Alemania)
- Ligue 1 (Francia)

### Plan Premium
- Liga Argentina
- Copa Libertadores
- Copa Sudamericana
- Todas las ligas europeas
- Y más...

## 💰 Planes y Precios

### Plan Premium Mensual
- 💵 $2.99/mes
- Todas las funciones premium

### Plan Premium Anual
- 💵 $29.99/año (2 meses gratis)
- Todas las funciones premium

### Plan Pro Mensual
- 💵 $4.99/mes
- Todo lo de Premium + soporte prioritario

## 🔧 Panel de Administración

### Funciones Disponibles
- 📊 Estadísticas del bot
- 👥 Gestión de usuarios
- 📢 Mensajes masivos
- 💎 Gestión de suscripciones premium
- 🔧 Configuración del bot
- 📋 Logs del sistema

### Acceso
Solo usuarios con ID agregado en `ADMIN_CONFIG['admin_ids']`

## 📊 Base de Datos

El bot utiliza SQLite para almacenar:
- Información de usuarios
- Consultas diarias
- Alertas personalizadas
- Estadísticas de uso
- Historial de pagos

### Backup Automático
La base de datos se respalda automáticamente cada 24 horas.

## 🔔 Sistema de Alertas

### Alertas Automáticas
- ⚽ Goles en vivo
- 🏁 Finales de partido
- 🔴 Tarjetas rojas

### Alertas Personalizadas (Premium)
- Goles de equipos específicos
- Partidos de ligas específicas
- Eventos personalizados

## 📈 Monitoreo

El bot monitorea partidos en vivo cada 60 segundos y envía alertas automáticas a todos los usuarios registrados.

## 🛡️ Seguridad

- Validación de tokens
- Límites de consultas por plan
- Protección contra spam
- Logs de actividad
- Backup automático

## 🔄 Actualizaciones

### Versión 2.0 (Actual)
- Sistema de suscripciones premium
- Panel de administración
- Base de datos SQLite
- Funciones avanzadas
- Monitoreo mejorado

### Próximas Funciones
- Integración con pasarelas de pago
- API REST para gestión
- Dashboard web
- Más ligas y competiciones
- Análisis predictivo avanzado

## 📞 Soporte

Para soporte técnico o consultas sobre suscripciones:
- Contacta al administrador: @tu_usuario_admin
- Canal de soporte: @tu_canal_soporte

## 📄 Licencia

Este proyecto está desarrollado por Valentín Olivero.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📝 Changelog

### v2.0.0
- ✨ Sistema de suscripciones premium
- 🔧 Panel de administración completo
- 📊 Base de datos SQLite
- 🎯 Funciones avanzadas
- 🔔 Alertas personalizadas
- 📈 Monitoreo mejorado

### v1.0.0
- 🎉 Lanzamiento inicial
- ⚽ Alertas básicas de goles
- 📅 Partidos de hoy
- 🏆 Tabla de posiciones

---

**Desarrollado con ❤️ por Valentín Olivero** 