from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.services.ticket_service import TicketService
from app.services.ticket_tramite_service import TicketTramiteService

anuncios_bp = Blueprint("anuncios", __name__, url_prefix="/anuncios")

@anuncios_bp.route("/")
def listar_anuncios():
    return render_template("anuncios/pantalla.html")