# Paquete de módulos

# Clases de modelo — deben importarse para que SQLAlchemy las registre
# para resolución de relationship() basada en strings entre archivos.
from modules.usuario import Usuario  # noqa: F401
from modules.usuario_final import UsuarioFinal, Claustro  # noqa: F401
from modules.usuario_admin import UsuarioAdmin, RolAdmin  # noqa: F401
from modules.departamento import Departamento  # noqa: F401
from modules.reclamo import Reclamo, EstadoReclamo  # noqa: F401
from modules.adherente_reclamo import AdherenteReclamo  # noqa: F401
from modules.historial_estado_reclamo import HistorialEstadoReclamo  # noqa: F401
from modules.derivacion_reclamo import DerivacionReclamo  # noqa: F401
from modules.notificacion_usuario import NotificacionUsuario  # noqa: F401

# Módulos de infraestructura
from modules.clasificador import clasificador, Clasificador
from modules.classifier import ClaimsClassifier
from modules.similitud import buscador_similitud, BuscadorSimilitud
from modules.manejador_imagen import ManejadorImagen

# Módulos generadores
from modules.generador_analiticas import GeneradorAnaliticas
from modules.generador_reportes import crear_reporte, Reporte, ReporteHTML, ReportePDF

# Módulos auxiliares
from modules.ayudante_admin import AyudanteAdmin
