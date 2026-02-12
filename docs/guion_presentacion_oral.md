# Guion de Presentación Oral - Sistema de Gestión de Reclamos
## Defensa del Trabajo Práctico

---

## 1. Introducción y Descripción del Problema

El proyecto que desarrollamos es un **sistema de atención y seguimiento de reclamos para la Facultad de Ingeniería de la UNER**.

El propósito principal es permitir a los usuarios finales —estudiantes, docentes y personal administrativo— **registrar reclamos fácilmente** sobre problemas, faltantes o desperfectos en las áreas comunes del edificio.

Además, brinda a los jefes de departamento y a la secretaría técnica una **herramienta para gestionar y resolver** estos reclamos de manera eficiente.

La idea central es **mejorar la trazabilidad, la transparencia y la participación** en el seguimiento de reclamos, facilitando la comunicación entre quienes detectan un problema y quienes pueden resolverlo.

---

## 2. Funcionamiento General del Programa

El sistema es una **aplicación web desarrollada con Flask**.

Los usuarios pueden **registrarse, iniciar sesión, crear nuevos reclamos o adherirse** a reclamos similares ya existentes.

Cuando un usuario crea un reclamo, la aplicación **lo clasifica automáticamente** usando un modelo de Machine Learning provisto por la cátedra (`data/claims_clf.pkl`) y lo dirige al departamento correspondiente.

Los responsables de cada área acceden a un **panel de administración** donde pueden visualizar los reclamos de su departamento, modificar su estado, derivarlos a otros departamentos si es necesario, y generar reportes con estadísticas.

Además, el sistema permite **detectar reclamos similares** utilizando TF-IDF y similitud del coseno (umbral 0.25), **enviar notificaciones** automáticas cuando cambia el estado de un reclamo, y **exportar reportes en formato HTML y PDF** con estadísticas por departamento.

---

## 3. Explicación del Diseño y Diagrama de Clases

Ahora voy a pasar a explicar el diseño del sistema, que se refleja en el diagrama de clases que está en pantalla (`docs/class.puml`).

El sistema está organizado siguiendo una **arquitectura en capas** y principios de **diseño orientado a objetos**.

### Clases de Dominio

En la base del sistema tenemos las **clases de dominio** que representan los conceptos principales de la aplicación:

- **`Usuario`** (clase base abstracta): Representa un usuario del sistema. Utiliza una metaclase combinada `MetaModeloABC` (que une `ABCMeta` con `type(db.Model)`) para resolver el conflicto de metaclases entre ABC y SQLAlchemy. Encapsula datos comunes como correo, nombre_usuario y hash_contrasena. Define la property abstracta `nombre_completo` que las subclases deben implementar.
  - **`UsuarioFinal`**: Usuario final (estudiantes, docentes, no docentes). Hereda de `Usuario` y agrega el atributo `claustro` (enum `Claustro`: ESTUDIANTE, DOCENTE, PAYS). Su `nombre_completo` retorna `"{nombre} {apellido} - {claustro.value}"`.
  - **`UsuarioAdmin`**: Usuario administrador (jefes de departamento, secretaría técnica). Hereda de `Usuario` y agrega `rol_admin` (enum `RolAdmin`: JEFE_DEPARTAMENTO, SECRETARIO_TECNICO) y `departamento_id`. Su `nombre_completo` retorna `"{nombre} {apellido} - {rol_admin.value}"`. Tiene properties `es_jefe_departamento` y `es_secretario_tecnico`.

Aquí aplicamos **herencia con Single Table Inheritance**: todas las clases `Usuario` se almacenan en una sola tabla `usuario` con un discriminador `tipo_usuario` para diferenciar el tipo.

- **`Reclamo`**: Representa un reclamo, con atributos como `detalle`, `estado` (enum `EstadoReclamo`: INVALIDO, PENDIENTE, EN_PROCESO, RESUELTO), `departamento_id`, `ruta_imagen`, `creado_en`, `actualizado_en`, y relaciones a su creador y departamento.

- **`Departamento`**: Representa un departamento de la facultad (Mantenimiento, Infraestructura, Sistemas, Secretaría Técnica). Tiene atributos `nombre`, `nombre_mostrar` y `es_secretaria_tecnica`.

### Relaciones Entre Entidades

**Composición (Reclamo → HistorialEstadoReclamo, AdherenteReclamo, DerivacionReclamo):**

La clase `Reclamo` tiene relaciones de **composición** con:
- **`HistorialEstadoReclamo`**: Almacena el historial de cambios de estado (`estado_anterior`, `estado_nuevo`, `cambiado_en`). Si elimino un reclamo, su historial también se elimina (`cascade="all, delete-orphan"`).
- **`AdherenteReclamo`**: Tabla intermedia que modela la relación muchos a muchos entre usuarios y reclamos (adhesión). Incluye `UniqueConstraint("reclamo_id", "usuario_id")` para evitar duplicados. Si elimino el reclamo, se eliminan todas sus adhesiones.
- **`DerivacionReclamo`**: Registra las derivaciones entre departamentos con `motivo`, `departamento_origen_id` y `departamento_destino_id`. Si elimino el reclamo, su historial de derivaciones también desaparece.

Esto aplica el **principio de composición**: estas entidades no tienen sentido sin un reclamo padre.

**Relación Muchos a Muchos (UsuarioFinal ↔ Reclamo):**

La **relación muchos a muchos** entre usuarios y reclamos se da cuando un usuario se adhiere a un reclamo creado por otro. Se modela con la tabla intermedia **`AdherenteReclamo`**.

### Arquitectura del Sistema

La lógica de negocio está integrada directamente en los **modelos mediante métodos estáticos** y en **clases de servicio especializadas**:

- **`Reclamo`** (en `modules/reclamo.py`): Incluye métodos estáticos como `crear()`, `actualizar_estado()`, `agregar_adherente()`, `quitar_adherente()`, `obtener_por_id()`, `obtener_pendientes()`, `obtener_por_usuario()`, etc. Utiliza el clasificador ML para asignar automáticamente el departamento.

- **`Clasificador`** (en `modules/clasificador.py`): Wrapper del clasificador provisto por la cátedra. Carga el modelo desde `data/claims_clf.pkl` y expone el método `clasificar()`. Instancia global: `clasificador`.

- **`BuscadorSimilitud`** (en `modules/similitud.py`): Calcula la similitud entre reclamos usando TF-IDF y similitud del coseno. Solo busca entre reclamos PENDIENTES. Instancia global: `buscador_similitud`.

- **`NotificacionUsuario`** (en `modules/notificacion_usuario.py`): Gestiona notificaciones. Métodos: `obtener_pendientes_usuario()`, `obtener_conteo_no_leidas()`, `marcar_notificacion_como_leida()`, `marcar_todas_como_leidas_usuario()`.

- **`Reporte`** (ABC) → **`ReporteHTML`**, **`ReportePDF`** (en `modules/generador_reportes.py`): Patrón ABC + Factory. La clase abstracta `Reporte` define `generar()` como método abstracto. La factory function `crear_reporte()` instancia el tipo correcto según el formato.

- **`GeneradorAnaliticas`** (en `modules/generador_analiticas.py`): Genera gráficos (torta, nube de palabras) y estadísticas. Todos los métodos son estáticos.

- **`ManejadorImagen`** (en `modules/manejador_imagen.py`): Gestiona validación y guardado de imágenes.

- **`AyudanteAdmin`** (en `modules/ayudante_admin.py`): Funciones auxiliares para el panel administrativo: `obtener_reclamos_para_admin()`, `obtener_reclamo_para_admin()`, `actualizar_estado_reclamo()`.

- **`DerivacionReclamo`** (en `modules/derivacion_reclamo.py`): Gestiona derivaciones con `derivar()`, `obtener_historial_reclamo()`, `obtener_departamentos_disponibles()`, `puede_derivar()`.

### Rutas

Todas las rutas están consolidadas en `modules/rutas.py` **sin usar blueprints**. Se usa endpoint namespacing con puntos (ej: `"admin.dashboard"`, `"claims.list"`, `"auth.end_user.login"`).

### Aplicación de Principios SOLID

**Principio de Abierto/Cerrado:**

El patrón ABC + Factory en los reportes permite agregar nuevos formatos (ej: CSV) sin modificar clases existentes. Solo se crea una nueva subclase de `Reporte` y se actualiza la factory function `crear_reporte()`.

**Principio de Inversión de Dependencias:**

Los modelos dependen de la **abstracción `db`** (SQLAlchemy), lo que permite cambiar de SQLite a PostgreSQL sin modificar el código de negocio. El `Reclamo` depende de la interfaz `clasificador.clasificar()`, no de la implementación concreta del modelo ML.

---

## 4. Justificación de Decisiones de Diseño

Elegimos integrar la **lógica de negocio directamente en los modelos** (métodos estáticos) para mantener la cohesión y simplicidad. Cada modelo sabe cómo crear, consultar y modificar sus propias instancias.

La **modularidad** hace que el sistema sea más fácil de entender y extender. Por ejemplo:
- Si quiero cambiar el algoritmo de clasificación, solo modifico `Clasificador` en `modules/clasificador.py`.
- Si quiero agregar un nuevo formato de reporte, creo una nueva subclase de `Reporte`.
- Si quiero cambiar la base de datos, solo modifico la configuración de SQLAlchemy en `modules/config.py`.

Utilizamos **decoradores personalizados** (`@admin_requerido`, `@usuario_final_requerido`, `@rol_admin_requerido`) para aplicar el **principio DRY** en el control de acceso, evitando repetir código de verificación de permisos en cada ruta.

La **metaclase `MetaModeloABC`** resuelve el conflicto entre `ABCMeta` y la metaclase de `db.Model`, permitiendo que `Usuario` sea abstracto y a la vez un modelo de SQLAlchemy.

---

## 5. Seguridad y Robustez

### Seguridad

Implementamos **seguridad mediante Flask-Login** para autenticar usuarios y proteger rutas con `@login_required`.

También usamos **control de acceso por rol**:
- Los usuarios finales solo pueden crear y consultar sus propios reclamos.
- Los jefes de departamento pueden gestionar reclamos de su departamento.
- La secretaría técnica puede gestionar todos los reclamos y derivarlos.

Esto se implementa con decoradores como `@admin_requerido`, `@usuario_final_requerido` y la función `puede_gestionar_reclamo()`.

Las contraseñas se almacenan usando **`werkzeug.security.generate_password_hash`** con salting automático.

Evitamos inyecciones SQL usando **SQLAlchemy ORM**, que parametriza automáticamente las consultas.

### Robustez

El sistema **maneja errores comunes**, como:
- Intentos de crear reclamos con detalles vacíos o muy cortos.
- Intentos de un usuario de adherirse dos veces al mismo reclamo (captura `IntegrityError`).
- Intentos de acceder a reclamos de otros departamentos sin permisos.
- Errores en la clasificación automática (fallback a secretaría técnica).

Todos los errores muestran **mensajes claros al usuario** mediante Flask flash messages.

---

## 6. Pruebas Realizadas

Realizamos **pruebas unitarias** utilizando el módulo **`unittest`** y organizándolas según el patrón **AAA (Arrange, Act, Assert)**.

### Ejemplos de Pruebas

**Pruebas de Reclamos (`tests/test_reclamo.py`):**
- Testeamos la **creación de reclamos** y validamos que se asignen correctamente al departamento.
- Verificamos la **lógica de adherencia**, asegurando que un usuario no pueda adherirse más de una vez.
- Probamos que **no se puedan crear reclamos con detalles vacíos**.

**Pruebas del Clasificador (`tests/test_clasificador_unit.py`):**
- Validamos que el **clasificador se entrene correctamente** con datos de ejemplo.
- Probamos la **clasificación de nuevos reclamos** y verificamos que retorne el departamento correcto.

**Pruebas de Similitud (`tests/test_similitud_unit.py`):**
- Verificamos que el **BuscadorSimilitud** detecte correctamente reclamos parecidos.
- Probamos el **umbral de similitud** (0.25) para evitar falsos positivos.

**Pruebas de Notificaciones (`tests/test_notificacion.py`):**
- Validamos que se **creen notificaciones automáticamente** cuando cambia el estado.
- Verificamos marcado como leídas.

**Pruebas de Admin y Reportes (`tests/test_admin_y_reportes.py`):**
- Probamos la **generación de reportes** y el filtrado por departamento.
- Validamos el acceso del panel administrativo.

**Pruebas de Derivaciones (`tests/test_derivacion_reclamo.py`):**
- Verificamos que los **reclamos se transfieran correctamente** entre departamentos.
- Validamos que solo secretario técnico pueda derivar.

Usamos una **base de datos SQLite en memoria** (`sqlite:///:memory:`) para mantener aisladas las pruebas.

Implementamos una clase base **`CasoTestBase`** en `tests/conftest.py` que configura el entorno de pruebas con `setUp()` y limpia con `tearDown()`.

---

## 7. Cumplimiento de Requisitos y Posibles Mejoras

El sistema cumple con **todos los requisitos funcionales**:
- ✅ Creación de reclamos con clasificación automática
- ✅ Adhesión a reclamos existentes
- ✅ Detección de reclamos similares
- ✅ Gestión administrativa por departamento
- ✅ Derivación entre departamentos
- ✅ Notificaciones automáticas
- ✅ Generación de reportes con estadísticas (HTML y PDF)
- ✅ Control de acceso por roles

### Posibles Mejoras Futuras

- **Notificaciones por email**: Enviar emails automáticos cuando cambia el estado de un reclamo.
- **Filtros avanzados**: Búsqueda por rango de fechas, múltiples estados, palabras clave.
- **Dashboard con gráficos interactivos**: Agregar gráficos dinámicos con Chart.js o Plotly.
- **API REST**: Exponer endpoints REST para integración con otras aplicaciones.
- **Autorización más granular**: Permisos más detallados (ej: moderadores).

---

## 8. Demostración

Ahora, si les parece, les muestro el sistema funcionando:

### 8.1. Registro y Login de Usuarios

Voy a registrar un nuevo usuario final como estudiante:
- Navego a `/register`
- Completo el formulario con nombre, apellido, email, username, contraseña y claustro
- El sistema valida los datos y crea la cuenta con `UsuarioFinal.registrar()`
- Inicio sesión con las credenciales

### 8.2. Creación de Reclamo

Como usuario final logueado:
- Navego a `/claims/create`
- Escribo el detalle del reclamo: "Se rompió la ventana del aula 102"
- El sistema **clasifica automáticamente** el reclamo usando `Reclamo._clasificar_departamento()` y lo asigna al departamento correspondiente
- Puedo subir una imagen del problema (opcional) — procesada por `ManejadorImagen`
- El reclamo se crea con estado PENDIENTE

### 8.3. Detección de Similitud y Adhesión

Voy a crear otro reclamo similar:
- Detalle: "La ventana del aula 102 está rota"
- El sistema **detecta que hay un reclamo similar** usando `buscador_similitud.buscar_reclamos_similares()`
- Me sugiere adherirme en lugar de crear uno duplicado
- Me adhiero al reclamo existente con `Reclamo.agregar_adherente()`
- La property `cantidad_adherentes` aumenta

### 8.4. Panel de Administración

Ahora inicio sesión como jefe del departamento:
- Navego a `/admin/` (endpoint `admin.dashboard`)
- Veo estadísticas del departamento usando `Reclamo.obtener_conteos_dashboard_departamento()`
- Veo la lista de reclamos en `/admin/claims` usando `AyudanteAdmin.obtener_reclamos_para_admin()`
- Selecciono un reclamo y veo su detalle completo
- Cambio el estado de PENDIENTE a EN_PROCESO usando `AyudanteAdmin.actualizar_estado_reclamo()`
- El sistema **crea una notificación automática** para el creador y adherentes

### 8.5. Derivación de Reclamo

Si el reclamo corresponde a otro departamento (como secretario técnico):
- Desde el detalle del reclamo, selecciono "Derivar"
- `DerivacionReclamo.puede_derivar()` verifica que soy secretario técnico
- `DerivacionReclamo.obtener_departamentos_disponibles()` muestra departamentos disponibles
- Agrego un motivo y ejecuto `DerivacionReclamo.derivar()`
- El reclamo se transfiere y se registra en el historial

### 8.6. Notificaciones

Como usuario final:
- Navego a `/notifications` (endpoint `users.notifications`)
- Veo notificaciones obtenidas con `NotificacionUsuario.obtener_pendientes_usuario()`
- Veo que el reclamo cambió de PENDIENTE a EN_PROCESO
- Marco como leídas con `NotificacionUsuario.marcar_notificacion_como_leida()`

### 8.7. Exportación de Reportes

Como administrador:
- Navego a `/admin/reports`
- Selecciono formato (HTML o PDF)
- `crear_reporte()` instancia `ReporteHTML` o `ReportePDF` (patrón Factory)
- El reporte se genera con `reporte.generar()` (polimorfismo)
- Descargo el archivo con estadísticas y listado de reclamos

### 8.8. Control de Acceso y Manejo de Errores

Demuestro la seguridad del sistema:
- Intento acceder a `/admin/` como usuario final → `@admin_requerido` **redirige**
- Intento adherirme dos veces → **IntegrityError capturado**: "Ya estás adherido a este reclamo"
- Intento crear reclamo con detalle vacío → **Muestra error de validación**

---

## Resumen Final

En resumen, el sistema de gestión de reclamos:

- **Resuelve un problema real** de la facultad: gestionar reclamos de forma organizada
- **Aplica principios de OOP**: herencia, polimorfismo, encapsulamiento, composición
- **Usa clases abstractas (ABC)**: `Usuario` con `MetaModeloABC`, `Reporte` con factory function
- **Sigue principios SOLID**: SRP, DIP, Open/Closed
- **Utiliza Machine Learning**: Modelo provisto por la cátedra para clasificación automática
- **Implementa seguridad robusta**: autenticación, control de acceso por roles, contraseñas encriptadas
- **Está bien testeado**: pruebas unitarias con unittest siguiendo patrón AAA
- **Es escalable y mantenible**: modularidad, bajo acoplamiento

Gracias por su atención. ¿Tienen alguna pregunta?

---

## Notas de Apoyo (No leer, solo referencia)

### Archivos Clave a Mencionar

- **Diagrama de clases:** `docs/class.puml`
- **Modelos:** `modules/usuario.py`, `modules/usuario_final.py`, `modules/usuario_admin.py`, `modules/reclamo.py`, `modules/departamento.py`
- **Módulos especializados:** `modules/clasificador.py`, `modules/similitud.py`, `modules/generador_analiticas.py`, `modules/generador_reportes.py`
- **Rutas:** `modules/rutas.py` (todas las rutas consolidadas, sin blueprints)
- **Tests:** `tests/test_adherente_reclamo.py`, `tests/test_clasificador_unit.py`, `tests/test_historial_estado.py`
- **Configuración:** `run.py` (punto de entrada), `modules/config.py` (factory pattern, db, login_manager)

### Conceptos Clave a Mencionar

- Single Table Inheritance (Usuario → UsuarioFinal/UsuarioAdmin)
- MetaModeloABC (ABCMeta + type(db.Model))
- ABC para Reporte → ReporteHTML, ReportePDF + factory function crear_reporte()
- Composición con cascade="all, delete-orphan"
- Relación muchos a muchos (AdherenteReclamo con UniqueConstraint)
- Clasificador provisto por cátedra (data/claims_clf.pkl)
- Similitud del coseno (umbral 0.25, solo reclamos PENDIENTES)
- Patrón AAA en tests
- unittest con CasoTestBase, setUp/tearDown
- Flask-Login para autenticación
- SQLAlchemy ORM con DeclarativeBase
- Principios SOLID (SRP, DIP, OCP)
- Decoradores: @admin_requerido, @usuario_final_requerido, @rol_admin_requerido
