from flask import Blueprint, render_template


participant_bp = Blueprint("participant", __name__, url_prefix="/participante")


@participant_bp.get("/")
def join():
    return render_template("participant/join.html")


@participant_bp.get("/sala")
def room():
    return render_template("participant/room.html")
