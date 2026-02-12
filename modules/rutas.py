from __future__ import annotations

import os
from datetime import datetime
from typing import Type

from flask import (
    Response, flash, jsonify, redirect, render_template, request,
    send_from_directory, session, url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from modules.config import app, db, login_manager
from modules.usuario_admin import RolAdmin, UsuarioAdmin
from modules.reclamo import Reclamo, EstadoReclamo
from modules.derivacion_reclamo import DerivacionReclamo
from modules.departamento import Departamento
from modules.usuario_final import Claustro, UsuarioFinal
from modules.usuario import Usuario
from modules.notificacion_usuario import NotificacionUsuario
from modules.ayudante_admin import AyudanteAdmin
from modules.generador_analiticas import GeneradorAnaliticas
from modules.manejador_imagen import ManejadorImagen
from modules.similitud import buscador_similitud
from modules.utils.decoradores import (
    admin_requerido, puede_gestionar_reclamo, usuario_final_requerido,
)


# ── Helpers privados ─────────────────────────────────────────────

def _manejar_login(
    clase_usuario: Type[Usuario], ruta_exito: str, ruta_fallo: str, plantilla: str,
):
    if request.method == "GET":
        return render_template(plantilla)
    #sino es un GET obligatoriamente va a ser un POST por lo que saltea este if

    nombre_usuario = request.form["username"]
    contrasena = request.form["password"]
    usuario = clase_usuario.autenticar(nombre_usuario, contrasena) 
    if usuario:
        login_user(usuario)
        flash("Has iniciado sesión correctamente", "success")
        return redirect(url_for(ruta_exito))

    flash("Usuario o contraseña incorrectos", "error")
    return redirect(url_for(ruta_fallo))


def _manejar_subida_imagen() -> str | None:
    if "image" in request.files:
        archivo = request.files["image"]
        if archivo and archivo.filename != "":
            ruta_guardada, error = ManejadorImagen.guardar_imagen_reclamo(archivo)
            if error:
                flash(f"Error con la imagen: {error}", "warning")
            else:
                return ruta_guardada
    return None


@login_manager.user_loader
def cargar_usuario(usuario_id):
    return Usuario.obtener_por_id(int(usuario_id))


@app.context_processor
def inyectar_notificaciones():
    if current_user.is_authenticated:
        conteo_no_leidas = NotificacionUsuario.obtener_conteo_no_leidas(current_user.id)
        ctx: dict = {"unread_notifications_count": conteo_no_leidas}
        if isinstance(current_user, UsuarioAdmin):
            ctx["is_technical_secretary"] = current_user.es_secretario_tecnico
        return ctx
    return {"unread_notifications_count": 0}


@app.route("/uploads/<path:filename>")
def archivo_subido(filename):
    directorio_subidas = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "static", "uploads"
    )
    return send_from_directory(directorio_subidas, filename)


@app.route("/", endpoint="main.index")
@login_required
def indice():
    return render_template("index.html", user=current_user)


@app.route("/register", methods=["GET", "POST"], endpoint="auth.end_user.register")
def registrar():
    if request.method == "GET":
        return render_template("auth/register.html")

    nombre = request.form["first_name"]
    apellido = request.form["last_name"]
    correo = request.form["email"]
    nombre_usuario = request.form["username"]
    valor_claustro = request.form["cloister"]
    contrasena = request.form["password"]
    contrasena_repetida = request.form["repeated_password"]
    if contrasena != contrasena_repetida:
        flash("Las contraseñas no coinciden.", "error")
        return redirect(url_for("auth.end_user.register"))
    try:
        claustro = Claustro(valor_claustro)
    except ValueError:
        flash("Claustro Inválido", "error")
        return render_template("auth/register.html")
    usuario, error = UsuarioFinal.registrar(
        nombre=nombre, apellido=apellido, correo=correo,
        nombre_usuario=nombre_usuario, claustro=claustro, contrasena=contrasena,
    )
    if error:
        flash(error, "error")
        return render_template("auth/register.html")
    flash("Usuario registrado exitosamente. Por favor inicie sesión.", "success")
    return redirect(url_for("auth.end_user.login"))


@app.route("/login", methods=["GET", "POST"], endpoint="auth.end_user.login")
def login():
    return _manejar_login(
        clase_usuario=UsuarioFinal, ruta_exito="main.index",
        ruta_fallo="auth.end_user.login", plantilla="auth/login.html",
    )


@app.route("/logout", methods=["GET", "POST"], endpoint="auth.end_user.logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "info")
    return redirect(url_for("main.index"))


@app.route("/admin/login", methods=["GET", "POST"], endpoint="auth.admin.login")
def admin_login():
    if request.method == "GET" and current_user.is_authenticated and isinstance(current_user, UsuarioAdmin):
        return redirect(url_for("admin.dashboard"))
    return _manejar_login(
        clase_usuario=UsuarioAdmin, ruta_exito="admin.dashboard",
        ruta_fallo="auth.admin.login", plantilla="admin/login.html",
    )


@app.route("/admin/", endpoint="admin.dashboard")
@admin_requerido
def admin_dashboard():
    usuario_admin: UsuarioAdmin = current_user
    departamentos = Departamento.obtener_para_admin(usuario_admin)
    conteos_dashboard = Reclamo.obtener_conteos_dashboard(departamentos)
    conteos_por_depto = Reclamo.obtener_conteos_dashboard_departamento(departamentos)
    stats_depto = [
        {
            "department": depto,
            "total": conteos_por_depto.get(depto.id, {}).get("total", 0),
            "pending": conteos_por_depto.get(depto.id, {}).get("pendientes", 0),
            "in_progress": conteos_por_depto.get(depto.id, {}).get("en_proceso", 0),
            "resolved": conteos_por_depto.get(depto.id, {}).get("resueltos", 0),
            "invalid": conteos_por_depto.get(depto.id, {}).get("invalidos", 0),
        }
        for depto in departamentos
    ]
    return render_template(
        "admin/dashboard.html", dept_stats=stats_depto,
        total_claims=conteos_dashboard["total_reclamos"],
        pending_claims=conteos_dashboard["reclamos_pendientes"],
        in_progress_claims=conteos_dashboard["reclamos_en_proceso"],
        resolved_claims=conteos_dashboard["reclamos_resueltos"],
        invalid_claims=conteos_dashboard["reclamos_invalidos"],
    )


@app.route("/admin/help", endpoint="admin.help")
@admin_requerido
def admin_help():
    return render_template("admin/help.html")


@app.route("/admin/claims", endpoint="admin.claims_list")
@admin_requerido
def admin_claims_list():
    usuario_admin: UsuarioAdmin = current_user
    reclamos = AyudanteAdmin.obtener_reclamos_para_admin(usuario_admin)
    ids_adherentes_por_reclamo = {
        reclamo.id: Reclamo.obtener_ids_adherentes(reclamo.id) for reclamo in reclamos
    }
    return render_template(
        "admin/claims_list.html", claims=reclamos, supporters_ids_by_claim=ids_adherentes_por_reclamo,
    )


@app.route("/admin/claims/<int:claim_id>", endpoint="admin.claim_detail")
@admin_requerido
def admin_claim_detail(claim_id: int):
    usuario_admin: UsuarioAdmin = current_user
    reclamo = AyudanteAdmin.obtener_reclamo_para_admin(usuario_admin, claim_id)
    if reclamo is None:
        flash("Reclamo no encontrado o sin permisos para verlo", "error")
        return redirect(url_for("admin.claims_list"))
    ids_adherentes = Reclamo.obtener_ids_adherentes(reclamo.id)
    departamentos_disponibles = []
    puede_derivar = DerivacionReclamo.puede_derivar(usuario_admin)
    if puede_derivar:
        departamentos_disponibles = DerivacionReclamo.obtener_departamentos_disponibles(reclamo.departamento_id)
    derivaciones = DerivacionReclamo.obtener_historial_reclamo(reclamo.id)
    return render_template(
        "admin/claim_detail.html", claim=reclamo, supporters_ids=ids_adherentes,
        can_transfer=puede_derivar, available_departments=departamentos_disponibles, transfers=derivaciones,
    )


@app.route("/admin/analytics", endpoint="admin.analytics")
def admin_analytics():
    usuario_admin: UsuarioAdmin = current_user
    departamentos = Departamento.obtener_para_admin(usuario_admin)
    datos_analiticas = GeneradorAnaliticas.obtener_analiticas_completas(departamentos)
    # Adaptar claves para template
    stats_template = {
        "total_claims": datos_analiticas["estadisticas"].get("total_reclamos", 0),
        "status_counts": datos_analiticas["estadisticas"].get("conteos_estado", {}),
        "status_percentages": datos_analiticas["estadisticas"].get("porcentajes_estado", {}),
    }
    return render_template(
        "admin/analytics.html",
        stats=stats_template, pie_chart=datos_analiticas["grafico_torta"],
        wordcloud=datos_analiticas["nube_palabras"], keywords=datos_analiticas["palabras_clave"],
        departments=departamentos,
    )


@app.route("/admin/reports", endpoint="admin.reports")
def admin_reports():
    usuario_admin: UsuarioAdmin = current_user
    departamentos = Departamento.obtener_para_admin(usuario_admin)
    return render_template("admin/reports.html", departments=departamentos)


@app.route("/admin/reports/download", endpoint="admin.download_report")
def admin_download_report():
    from modules.generador_reportes import crear_reporte

    usuario_admin: UsuarioAdmin = current_user
    departamentos = Departamento.obtener_para_admin(usuario_admin)
    formato_reporte = request.args.get("format", "html")

    reporte = crear_reporte(formato_reporte, departamentos, usuario_admin.es_secretario_tecnico)
    contenido = reporte.generar()
    tipo_contenido = "application/pdf" if formato_reporte == "pdf" else "text/html"
    if contenido is None:
        flash("No se pudo generar el reporte.", "error")
        return redirect(url_for("admin.reports"))
    return Response(
        contenido, mimetype=tipo_contenido,
        headers={
            f"Content-Disposition": f"attachment; filename=reporte_reclamos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{'pdf' if formato_reporte == 'pdf' else 'html'}"
        },
    )


@app.route(
    "/admin/claims/<int:claim_id>/transfers", methods=["GET", "POST"], endpoint="admin.transfers",
)
@admin_requerido
def admin_transfers(claim_id: int):
    usuario_admin: UsuarioAdmin = current_user

    reclamo = AyudanteAdmin.obtener_reclamo_para_admin(usuario_admin, claim_id)
    if reclamo is None:
        flash("Reclamo no encontrado", "error")
        return redirect(url_for("admin.claims_list"))

    if request.method == "POST":
        if not (isinstance(usuario_admin, UsuarioAdmin) and usuario_admin.rol_admin == RolAdmin.SECRETARIO_TECNICO):
            flash("No tienes permisos para derivar reclamos", "error")
            return redirect(url_for("admin.claim_detail", claim_id=claim_id))

        departamento_destino_id = request.form.get("department_id", type=int)
        motivo = request.form.get("reason", "").strip()

        if not departamento_destino_id:
            flash("Debe seleccionar un departamento destino", "error")
            return redirect(url_for("admin.claim_detail", claim_id=claim_id))

        derivacion, error = DerivacionReclamo.derivar(
            reclamo_id=claim_id, departamento_destino_id=departamento_destino_id,
            derivado_por_id=usuario_admin.id, motivo=motivo,
        )

        if error:
            flash(f"Error al derivar reclamo: {error}", "error")
        else:
            flash("Reclamo derivado exitosamente", "success")

        return redirect(url_for("admin.claim_detail", claim_id=claim_id))

    derivaciones = DerivacionReclamo.obtener_historial_reclamo(claim_id)
    return render_template("admin/transfers.html", claim=reclamo, transfers=derivaciones)


@app.route("/claims", methods=["GET", "POST"], endpoint="claims.list")
def claims_list():
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Debes iniciar sesión para crear un reclamo", "error")
            return redirect(url_for("auth.end_user.login"))
        if not isinstance(current_user, UsuarioFinal):
            flash("Solo los usuarios finales pueden crear reclamos", "error")
            return redirect(url_for("admin.dashboard"))

        reclamo_pendiente = session.get("pending_claim")
        if not reclamo_pendiente:
            flash("Sesión expirada. Por favor, intente nuevamente.", "error")
            return redirect(url_for("claims.new"))

        detalle = reclamo_pendiente.get("detail")
        ruta_imagen = reclamo_pendiente.get("image_path")
        session.pop("pending_claim", None)

        reclamo, error = Reclamo.crear(
            usuario_id=current_user.id, detalle=detalle, ruta_imagen=ruta_imagen,
        )

        if error or not reclamo:
            if ruta_imagen:
                ManejadorImagen.eliminar_imagen_reclamo(ruta_imagen)
            error = error or "Error al crear el reclamo"
            flash(error, "error")
            return redirect(url_for("claims.new"))

        flash(f"Reclamo #{reclamo.id} creado exitosamente", "success")
        return redirect(url_for("claims.detail", id=reclamo.id))

    filtro_departamento = request.args.get("department", type=int)
    filtro_estado = request.args.get("status", type=str)

    estado_enum = None
    if filtro_estado:
        try:
            estado_enum = EstadoReclamo[filtro_estado.upper()]
        except KeyError:
            flash("Estado de reclamo no válido", "error")

    reclamos = Reclamo.obtener_todos_con_filtros(
        filtro_departamento=filtro_departamento, filtro_estado=estado_enum
    )
    departamentos = Departamento.obtener_todos()

    return render_template(
        "claims/list.html", claims=reclamos, departments=departamentos, 
        selected_department=filtro_departamento, selected_status=filtro_estado,
    )


@app.route("/claims/new", methods=["GET"], endpoint="claims.new")
@usuario_final_requerido
def claims_new():
    return render_template("claims/create.html")


@app.route("/claims/preview", methods=["POST"], endpoint="claims.preview")
@usuario_final_requerido
def claims_preview():
    detalle = request.form.get("detail", "").strip()

    if not detalle:
        flash("Debe proporcionar un detalle del reclamo", "error")
        return redirect(url_for("claims.new"))

    ruta_imagen = _manejar_subida_imagen()
    reclamos_similares = buscador_similitud.buscar_reclamos_similares(texto=detalle)

    session["pending_claim"] = {
        "detail": detalle, "image_path": ruta_imagen,
    }

    return render_template(
        "claims/preview.html", detail=detalle, similar_claims=reclamos_similares, image_path=ruta_imagen,
    )


@app.route("/claims/<int:id>", methods=["GET"], endpoint="claims.detail")
def claims_detail(id: int):
    reclamo = Reclamo.obtener_por_id(id)
    if not reclamo:
        flash("Reclamo no encontrado", "error")
        return redirect(url_for("claims.list"))

    es_adherente = False
    if current_user.is_authenticated:
        es_adherente = Reclamo.es_usuario_adherente(id, current_user.id)

    return render_template("claims/detail.html", claim=reclamo, is_supporter=es_adherente)


@app.route("/claims/<int:id>/supporters", methods=["POST"], endpoint="claims.add_supporter")
@usuario_final_requerido
def claims_add_supporter(id: int):
    exito, error = Reclamo.agregar_adherente(reclamo_id=id, usuario_id=current_user.id)
    if error:
        flash(error, "error")
    else:
        flash("Te has adherido al reclamo exitosamente", "success")
    return redirect(url_for("claims.detail", id=id))


@app.route("/claims/<int:id>/supporters/delete", methods=["POST"], endpoint="claims.remove_supporter")
@usuario_final_requerido
def claims_remove_supporter(id: int):
    exito, error = Reclamo.quitar_adherente(reclamo_id=id, usuario_id=current_user.id)
    if error:
        flash(error, "error")
    else:
        flash("Has dejado de adherirte al reclamo", "success")
    return redirect(url_for("claims.detail", id=id))


@app.route("/claims/<int:id>/status", methods=["POST"], endpoint="claims.update_status")
@admin_requerido
def claims_update_status(id: int):
    reclamo = Reclamo.obtener_por_id(id)
    if not reclamo:
        flash("Reclamo no encontrado", "error")
        return redirect(url_for("claims.list"))
    if not puede_gestionar_reclamo(reclamo):
        flash("No tienes permiso para gestionar este reclamo", "error")
        return redirect(url_for("claims.detail", id=id))

    nuevo_estado_str = request.form.get("status", "")
    if not nuevo_estado_str:
        flash("Debe proporcionar un estado", "error")
        return redirect(url_for("claims.detail", id=id))

    try:
        nuevo_estado = EstadoReclamo[nuevo_estado_str.upper()]
    except KeyError:
        flash("Estado no válido", "error")
        return redirect(url_for("claims.detail", id=id))

    exito, error = AyudanteAdmin.actualizar_estado_reclamo(current_user, id, nuevo_estado)
    if error:
        flash(error, "error")
    else:
        flash("Estado actualizado correctamente", "success")
    return redirect(url_for("admin.claim_detail", claim_id=id))


@app.route("/users/me/claims", methods=["GET"], endpoint="users.my_claims")
@usuario_final_requerido
def users_my_claims():
    reclamos = Reclamo.obtener_por_usuario(current_user.id)
    return render_template("users/my_claims.html", claims=reclamos)


@app.route("/users/me/supported-claims", methods=["GET"], endpoint="users.my_supported_claims")
@usuario_final_requerido
def users_my_supported_claims():
    reclamos = Reclamo.obtener_adheridos_por_usuario(current_user.id)
    return render_template("users/my_supported_claims.html", claims=reclamos)


@app.route("/users/me/notifications", methods=["GET"], endpoint="users.notifications")
@usuario_final_requerido
def users_notifications():
    notificaciones_pendientes = NotificacionUsuario.obtener_pendientes_usuario(current_user.id)
    return render_template("users/notifications.html", notifications=notificaciones_pendientes)


@app.route(
    "/users/me/notifications/<int:notification_id>", methods=["POST"],
    endpoint="users.mark_notification_read",
)
@usuario_final_requerido
def users_mark_notification_read(notification_id):
    exito, error = NotificacionUsuario.marcar_notificacion_como_leida(notification_id, current_user.id)
    if error:
        flash(error, "error")
    else:
        flash("Notificación marcada como leída", "success")
    return redirect(url_for("users.notifications"))


@app.route(
    "/users/me/notifications/mark-all-read", methods=["POST"],
    endpoint="users.mark_all_notifications_read",
)
@usuario_final_requerido
def users_mark_all_notifications_read():
    conteo = NotificacionUsuario.marcar_todas_como_leidas_usuario(current_user.id)
    flash(f"Se marcaron {conteo} notificaciones como leídas", "success")
    return redirect(request.referrer or url_for("users.notifications"))
