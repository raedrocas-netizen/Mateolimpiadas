from flask import Flask

from config import Config
from extensions import socketio
from helper.database_implements import create_tables
from routes.api import api_bp
from routes.judge import judge_bp
from routes.main import main_bp
from routes.participant import participant_bp
from socket_events.competition_events import register_socket_events


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(main_bp)
    app.register_blueprint(judge_bp)
    app.register_blueprint(participant_bp)
    app.register_blueprint(api_bp)

    socketio.init_app(app)
    register_socket_events(socketio)

    with app.app_context():
        create_tables()

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
