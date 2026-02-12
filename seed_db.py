"""
Script para inicializar datos de prueba en la base de datos.
Ejecutar después de init_db.py para crear departamentos y usuarios admin.
"""

from modules.config import create_app, db
from modules.usuario_admin import RolAdmin, UsuarioAdmin
from modules.reclamo import Reclamo, EstadoReclamo
from modules.departamento import Departamento
from modules.usuario_final import Claustro, UsuarioFinal


def limpiar_base_datos():
    """Limpia todas las tablas de la base de datos para empezar de cero"""
    print("  Limpiando base de datos...")
    from modules.notificacion_usuario import NotificacionUsuario
    from modules.historial_estado_reclamo import HistorialEstadoReclamo
    from modules.adherente_reclamo import AdherenteReclamo
    from modules.derivacion_reclamo import DerivacionReclamo

    try:
        NotificacionUsuario.query.delete()
        HistorialEstadoReclamo.query.delete()
        AdherenteReclamo.query.delete()
        DerivacionReclamo.query.delete()
        Reclamo.query.delete()
        UsuarioFinal.query.delete()
        UsuarioAdmin.query.delete()
        Departamento.query.delete()
        db.session.commit()
        print("  ✓ Base de datos limpiada exitosamente")
    except Exception as e:
        db.session.rollback()
        print(f"  ! Error al limpiar base de datos: {e}")
        raise


def crear_departamentos():
    datos_departamentos = [
        {
            "nombre": "Secretario Informartico - secretario_informatico",
            "nombre_mostrar": "Secretario Informático",
            "es_secretaria_tecnica": False,
        },
        {
            "nombre": "Maestranza - maestranza",
            "nombre_mostrar": "Maestranza",
            "es_secretaria_tecnica": False,
        },
        {
            "nombre": "Secretario Técnico - secretario_tecnico",
            "nombre_mostrar": "Secretaría Técnica",
            "es_secretaria_tecnica": True,
        },
    ]

    creados = 0
    for datos_depto in datos_departamentos:
        existente = Departamento.query.filter_by(nombre=datos_depto["nombre"]).first()
        if not existente:
            depto = Departamento(**datos_depto)
            db.session.add(depto)
            creados += 1
            print(f"  ✓ Departamento '{datos_depto['nombre_mostrar']}' creado")
        else:
            print(f"  - Departamento '{datos_depto['nombre_mostrar']}' ya existe")

    db.session.commit()
    return creados


def crear_usuarios_admin():
    print("  2a. Creando secretario técnico...")
    secretaria = Departamento.query.filter_by(es_secretaria_tecnica=True).first()

    if secretaria:
        existente = UsuarioAdmin.query.filter_by(nombre_usuario="secretario_tecnico").first()
        if not existente:
            usuario = UsuarioAdmin(
                nombre="Secretario", apellido="Técnico",
                correo="secretario@sistema.local", nombre_usuario="secretario_tecnico",
                rol_admin=RolAdmin.SECRETARIO_TECNICO, departamento_id=secretaria.id,
            )
            usuario.establecer_contrasena("admin123")
            db.session.add(usuario)
            db.session.commit()
            print(f"     ✓ Usuario 'secretario_tecnico' creado")
        else:
            print(f"     - Usuario 'secretario_tecnico' ya existe")

    print("  2b. Creando jefes de departamento...")
    departamentos = Departamento.query.filter_by(es_secretaria_tecnica=False).all()
    creados = 0

    for depto in departamentos:
        identificador = depto.nombre.split(" - ")[-1].strip().lower()
        nombre_usuario = f"jefe_{identificador}"
        correo = f"jefe.{identificador}@sistema.local"
        existente = UsuarioAdmin.query.filter_by(nombre_usuario=nombre_usuario).first()
        if not existente:
            usuario = UsuarioAdmin(
                nombre="Jefe", apellido=depto.nombre_mostrar,
                correo=correo, nombre_usuario=nombre_usuario,
                rol_admin=RolAdmin.JEFE_DEPARTAMENTO, departamento_id=depto.id,
            )
            usuario.establecer_contrasena("admin123")
            db.session.add(usuario)
            creados += 1
            print(f"     ✓ Usuario '{nombre_usuario}' creado")
        else:
            print(f"     - Usuario '{nombre_usuario}' ya existe")

    db.session.commit()
    return creados + (1 if secretaria and not existente else 0)


def crear_usuarios_finales():
    datos_usuarios = [
        {"nombre": "User", "apellido": "One", "correo": "user1@estudiante.local", "nombre_usuario": "user1", "claustro": Claustro.ESTUDIANTE, "contrasena": "user123"},
        {"nombre": "User", "apellido": "Two", "correo": "user2@docente.local", "nombre_usuario": "user2", "claustro": Claustro.DOCENTE, "contrasena": "user123"},
        {"nombre": "User", "apellido": "Three", "correo": "user3@pays.local", "nombre_usuario": "user3", "claustro": Claustro.PAYS, "contrasena": "user123"},
        {"nombre": "User", "apellido": "Four", "correo": "user4@estudiante.local", "nombre_usuario": "user4", "claustro": Claustro.ESTUDIANTE, "contrasena": "user123"},
    ]

    creados = 0
    for datos_usuario in datos_usuarios:
        existente = UsuarioFinal.query.filter_by(nombre_usuario=datos_usuario["nombre_usuario"]).first()
        if not existente:
            contrasena = datos_usuario.pop("contrasena")
            usuario = UsuarioFinal(**datos_usuario)
            usuario.establecer_contrasena(contrasena)
            db.session.add(usuario)
            creados += 1
            print(f"  ✓ Usuario '{datos_usuario['nombre_usuario']}' creado")
        else:
            print(f"  - Usuario '{datos_usuario['nombre_usuario']}' ya existe")

    db.session.commit()
    return creados


def crear_reclamos_ejemplo():
    """Crea reclamos de prueba y actualiza estados usando servicios."""
    usuarios_finales = (
        db.session.query(UsuarioFinal)
        .filter(UsuarioFinal.nombre_usuario.in_(["user1", "user2", "user3", "user4"]))
        .order_by(UsuarioFinal.nombre_usuario.asc())
        .all()
    )

    secretario_informatico = db.session.query(Departamento).filter_by(
        nombre="Secretario Informartico - secretario_informatico"
    ).first()
    maestranza = db.session.query(Departamento).filter_by(
        nombre="Maestranza - maestranza"
    ).first()
    secretaria = db.session.query(Departamento).filter_by(es_secretaria_tecnica=True).first()

    if not all([secretario_informatico, maestranza, secretaria]) or len(usuarios_finales) < 1:
        print("  ! No se pueden crear reclamos: faltan usuarios o departamentos")
        return 0

    assert secretario_informatico is not None
    assert maestranza is not None
    assert secretaria is not None

    secretario_tecnico = db.session.query(UsuarioAdmin).filter_by(rol_admin=RolAdmin.SECRETARIO_TECNICO).first()
    jefe_informatico = db.session.query(UsuarioAdmin).filter_by(
        rol_admin=RolAdmin.JEFE_DEPARTAMENTO,
        departamento_id=secretario_informatico.id,
    ).first()
    jefe_maestranza = db.session.query(UsuarioAdmin).filter_by(
        rol_admin=RolAdmin.JEFE_DEPARTAMENTO,
        departamento_id=maestranza.id,
    ).first()

    if not all([secretario_tecnico, jefe_informatico, jefe_maestranza]):
        print("  ! No se pueden actualizar estados: faltan usuarios administrativos")
        return 0

    assert secretario_tecnico is not None
    assert jefe_informatico is not None
    assert jefe_maestranza is not None

    textos_depto: dict[int, list[str]] = {
        secretario_informatico.id: [
            "No hay internet en el laboratorio de informática",
            "La computadora del aula no enciende",
            "El proyector está fallando y se apaga",
            "No funciona el WiFi en el edificio B",
            "La impresora de la sala de profesores no imprime",
            "El sistema de sonido del auditorio no funciona",
            "No puedo acceder al campus virtual",
            "La red de internet está muy lenta",
            "El software de la computadora tiene virus",
            "No funciona el micrófono del salón",
            "La pantalla del proyector tiene líneas",
            "No se puede conectar la notebook al proyector",
            "El sistema de control de asistencia no funciona",
            "La cámara de videoconferencia no enciende",
            "No funciona el cable HDMI del proyector",
        ],
        maestranza.id: [
            "El aire acondicionado no funciona en el aula 301",
            "Se rompió la canilla del baño del segundo piso",
            "Las luces del pasillo están quemadas",
            "El ascensor hace ruidos extraños",
            "No sale agua caliente en los baños",
            "La puerta del salón no cierra correctamente",
            "El ventilador de techo no enciende",
            "Hay una gotera en el techo del laboratorio",
            "El inodoro del baño está tapado",
            "La cerradura de la puerta está rota",
            "Hay grietas en la pared del aula 205",
            "Las baldosas del piso están rotas y peligrosas",
            "Se necesita pintar las paredes del edificio",
            "Las escaleras están en mal estado",
            "La pintura de las aulas está descascarada",
        ],
        secretaria.id: [
            "Mi reclamo fue mal derivado y nadie lo atiende desde hace un mes",
            "Necesito hablar con autoridades sobre un problema que no resuelven",
            "Quiero presentar una queja formal sobre el servicio",
            "El departamento de maestranza no responde mis reclamos",
            "Este problema afecta a múltiples áreas y necesita coordinación",
            "Necesito que revisen el historial de mi reclamo porque figura como Resuelto y sigue igual",
            "El problema se repite hace semanas y no hay respuesta",
            "Solicito intervención de secretaría técnica por falta de seguimiento",
            "El reclamo quedó en Pendiente demasiado tiempo sin novedades",
            "Nadie se hace cargo del problema y necesito una solución formal",
        ],
    }

    ciclo_deptos = [secretario_informatico.id, maestranza.id, secretaria.id]
    plan_deptos: list[int] = []
    for _ in range(10):
        plan_deptos.extend(ciclo_deptos)

    depto_por_id = {
        secretario_informatico.id: secretario_informatico,
        maestranza.id: maestranza,
        secretaria.id: secretaria,
    }

    creados = 0
    reclamos_por_depto: dict[int, list[int]] = {depto_id: [] for depto_id in depto_por_id}

    indice_global = 1
    for usuario in usuarios_finales:
        for i in range(1, 11):
            if len(plan_deptos) == 0:
                break
            departamento_id = plan_deptos.pop(0)
            depto = depto_por_id[departamento_id]
            textos_base = textos_depto.get(departamento_id, [])
            texto_base = (
                textos_base[(indice_global - 1) % len(textos_base)]
                if len(textos_base) > 0
                else "Incidente reportado por el usuario"
            )
            detalle = f"{texto_base}"
            reclamo, error = Reclamo.crear(
                usuario_id=usuario.id, detalle=detalle,
                departamento_id=departamento_id, ruta_imagen=None,
            )
            if error or reclamo is None:
                print(f"  ! Error creando reclamo: {error}")
                continue
            creados += 1
            reclamos_por_depto[departamento_id].append(reclamo.id)
            indice_global += 1

    def _aplicar_estados(ids_reclamos, usuario_admin_id, invalidos_n, resueltos_n, en_proceso_n):
        if len(ids_reclamos) == 0:
            return
        idx = 0
        for _ in range(min(invalidos_n, len(ids_reclamos) - idx)):
            Reclamo.actualizar_estado(reclamo_id=ids_reclamos[idx], nuevo_estado=EstadoReclamo.INVALIDO, usuario_admin_id=usuario_admin_id)
            idx += 1
        for _ in range(min(resueltos_n, len(ids_reclamos) - idx)):
            Reclamo.actualizar_estado(reclamo_id=ids_reclamos[idx], nuevo_estado=EstadoReclamo.RESUELTO, usuario_admin_id=usuario_admin_id)
            idx += 1
        for _ in range(min(en_proceso_n, len(ids_reclamos) - idx)):
            Reclamo.actualizar_estado(reclamo_id=ids_reclamos[idx], nuevo_estado=EstadoReclamo.EN_PROCESO, usuario_admin_id=usuario_admin_id)
            idx += 1

    _aplicar_estados(reclamos_por_depto[secretario_informatico.id], jefe_informatico.id, invalidos_n=1, resueltos_n=3, en_proceso_n=2)
    _aplicar_estados(reclamos_por_depto[maestranza.id], jefe_maestranza.id, invalidos_n=1, resueltos_n=3, en_proceso_n=2)
    _aplicar_estados(reclamos_por_depto[secretaria.id], secretario_tecnico.id, invalidos_n=1, resueltos_n=3, en_proceso_n=2)

    return creados


def main():
    app = create_app()
    with app.app_context():
        print("\n=== Inicializando datos de prueba ===\n")
        print("0. Limpiando base de datos existente...")
        limpiar_base_datos()
        print()
        print("1. Creando departamentos...")
        conteo_deptos = crear_departamentos()
        print(f"   {conteo_deptos} departamentos nuevos creados\n")
        print("2. Creando usuarios administrativos...")
        conteo_admin = crear_usuarios_admin()
        print(f"   Total: {conteo_admin} usuarios administrativos\n")
        print("3. Creando usuarios finales...")
        conteo_usuarios = crear_usuarios_finales()
        print(f"   {conteo_usuarios} usuarios finales nuevos creados\n")
        print("4. Creando reclamos de prueba...")
        conteo_reclamos = crear_reclamos_ejemplo()
        print(f"   {conteo_reclamos} reclamos nuevos creados\n")
        print("=== Inicialización completada ===\n")

        print("Departamentos en el sistema:")
        for depto in Departamento.query.all():
            sufijo = " (Secretaría Técnica)" if depto.es_secretaria_tecnica else ""
            print(f"  - {depto.nombre_mostrar}{sufijo}")

        print("\nUsuarios administrativos:")
        for usuario in UsuarioAdmin.query.all():
            nombre_depto = usuario.departamento.nombre_mostrar if usuario.departamento else "Sin departamento"
            print(f"  - {usuario.nombre_usuario} ({usuario.rol_admin.value}) - {nombre_depto}")

        print("\nUsuarios finales:")
        for usuario in UsuarioFinal.query.all():
            print(f"  - {usuario.nombre_usuario} ({usuario.claustro.value})")

        print(f"\nReclamos creados: {Reclamo.query.count()}")
        print("  Se generaron reclamos en varios estados (Pendiente/En proceso/Resuelto/Inválido)")


if __name__ == "__main__":
    main()
