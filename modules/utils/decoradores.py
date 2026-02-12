"""Decoradores de permisos para control de acceso basado en roles"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from modules.usuario_admin import RolAdmin, UsuarioAdmin
from modules.usuario_final import UsuarioFinal


def usuario_final_requerido(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para acceder a esta página", "error")
            return redirect(url_for("auth.end_user.login"))
        if not isinstance(current_user, UsuarioFinal):
            flash("Esta sección es solo para usuarios finales.", "error")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)
    return funcion_decorada

# f = admin_help
def admin_requerido(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión como administrador", "error")
            return redirect(url_for("auth.admin.login"))
        if not isinstance(current_user, UsuarioAdmin):
            flash("Acceso denegado. Solo para administradores.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return funcion_decorada


def puede_gestionar_reclamo(reclamo):
    if not isinstance(current_user, UsuarioAdmin):
        return False
    return current_user.puede_acceder_reclamo(reclamo)
