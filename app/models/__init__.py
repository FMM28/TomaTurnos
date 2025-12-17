from .usuario import Usuario
from .area import Area
from .tramite import Tramite
from .ventanilla import Ventanilla
from .asignacion import Asignacion
from .ticket import Ticket
from .ticket_tramite import TicketTramite
from .atencion import Atencion
from app.extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))