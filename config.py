import os

import helper.super_global as sg


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "mateolimpiadas-web-secret")
    DATABASE_URL = os.getenv("DATABASE_URL")
    JUDGE_USERNAME = os.getenv("JUDGE_USERNAME", sg.JUDGE_USERNAME)
    JUDGE_PASSWORD = os.getenv("JUDGE_PASSWORD", sg.JUDGE_PASSWORD)
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")
