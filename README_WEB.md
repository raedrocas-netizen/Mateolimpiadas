# Olimpiadas del Conocimiento - Plataforma Web

Aplicacion web Flask migrada desde el proyecto Tkinter/TCP original, reutilizando las capas de datos, entidades y reglas de negocio.

## Requisitos

- Python 3.11+
- PostgreSQL
- Variable de entorno `DATABASE_URL`

## Instalacion local

```bash
pip install -r requirements.txt
set DATABASE_URL=postgresql://usuario:clave@host:5432/base
python app.py
```

## Render

Configurar:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --worker-class gthread --threads 8 --bind 0.0.0.0:$PORT app:app`
- Environment variable: `DATABASE_URL`

## Acceso

- Pantalla principal: `/`
- Participantes: `/participante/`
- Jueces: `/juez/login`

Credenciales por defecto del juez:

- Usuario: `computacionz12`
- Contrasena: `juecesimbpc`

Pueden sobrescribirse con `JUDGE_USERNAME` y `JUDGE_PASSWORD`.
