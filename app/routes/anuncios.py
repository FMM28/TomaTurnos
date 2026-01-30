from flask import Blueprint, render_template

anuncios_bp = Blueprint("anuncios", __name__, url_prefix="/anuncios")

@anuncios_bp.route("/")
def listar_anuncios():
    return render_template("anuncios/pantalla.html")