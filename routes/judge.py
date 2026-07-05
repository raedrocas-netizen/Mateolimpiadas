from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from helpers.ownership import is_owned
from logical_business.cuestionario_business import CuestionarioBusiness


judge_bp = Blueprint("judge", __name__, url_prefix="/juez")


def judge_required():
    return session.get("judge_authenticated") is True


@judge_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if (
                username == current_app.config["JUDGE_USERNAME"]
                and password == current_app.config["JUDGE_PASSWORD"]
        ):
            session["judge_authenticated"] = True
            return redirect(url_for("judge.name"))

        error = "Credenciales incorrectas."

    return render_template("judge/login.html", error=error)


@judge_bp.route("/nombre", methods=["GET", "POST"])
def name():
    if not judge_required():
        return redirect(url_for("judge.login"))

    if request.method == "POST":
        session["judge_name"] = request.form.get("judge_name", "").strip()
        return redirect(url_for("judge.dashboard"))

    return render_template("judge/name.html")


@judge_bp.get("/dashboard")
def dashboard():
    if not judge_required():
        return redirect(url_for("judge.login"))

    if not session.get("judge_name"):
        return redirect(url_for("judge.name"))

    return render_template(
        "judge/dashboard.html",
        judge_name=session.get("judge_name")
    )


@judge_bp.get("/cuestionario/<int:id_cuestionario>/preguntas")
def questionnaire_questions(id_cuestionario):
    if not judge_required():
        return redirect(url_for("judge.login"))

    if not session.get("judge_name"):
        return redirect(url_for("judge.name"))

    if not is_owned("cuestionarios", "id_cuestionario", id_cuestionario):
        return redirect(url_for("judge.dashboard"))

    cuestionario = CuestionarioBusiness().get_by_id(id_cuestionario)

    return render_template(
        "judge/questionnaire_questions.html",
        judge_name=session.get("judge_name"),
        cuestionario=cuestionario
    )


@judge_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
