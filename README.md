# Sistema de Gestión de Reclamos Universitarios

**Trabajo Práctico Final — Programación Orientada a Objetos**

Sistema web para la gestión de reclamos universitarios con clasificación automática, búsqueda por similitud, y panel administrativo.

---

## Funcionalidades Principales

- **Clasificación automática** de reclamos por departamento (modelo ML provisto por la cátedra)
- **Detección de reclamos similares** mediante TF-IDF y similitud del coseno
- **Sistema de adherentes** para que usuarios apoyen reclamos existentes
- **Notificaciones automáticas** al cambiar el estado de un reclamo
- **Panel administrativo** con roles (Jefe de Departamento / Secretario Técnico)
- **Reportes y analíticas** con gráficos y exportación a PDF

---

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate       # Linux/macOS

# 2. Instalar dependencias
pip install -r .\deps\requirements.txt

# 3. Inicializar base de datos y datos de prueba
python init_db.py
python seed_db.py

# 4. Ejecutar servidor
python server.py
```

Abrir en el navegador: **http://127.0.0.1:5000**

---

## Usuarios de Prueba

| Tipo | Usuario | Contraseña |
|------|---------|------------|
| Usuario Final | `user1`, `user2`, `user3`, `user4` | `user123` |
| Secretario Técnico | `secretario_tecnico` | `admin123` |
| Jefe de Departamento | `jefe_secretario_informatico`, `jefe_maestranza` | `admin123` |

> Los administradores inician sesión en `/admin/login`

---

## Clasificador Automático

El sistema utiliza un **clasificador provisto por la cátedra** (`data/claims_clf.pkl`) que asigna automáticamente cada reclamo a un departamento según su contenido.

> **Importante:** El modelo ya viene pre-entrenado y **no debe entrenarse localmente**. El archivo `modules/clasificador.py` simplemente carga el pickle y expone el método `clasificar()`.

---

## Ejecutar Tests

```bash
python -m unittest discover tests -v
```

---

## Estructura del Proyecto

> **Nota de arquitectura:** El proyecto utiliza un diseño de **rutas consolidadas** en `modules/rutas.py` sin blueprints de Flask, siguiendo un patrón más simple y directo para un proyecto académico de este alcance.

```
proyecto-final/
├── modules/              # Lógica de negocio y modelos
│   ├── config.py         # Configuración Flask y SQLAlchemy
│   ├── rutas.py          # Rutas consolidadas (sin blueprints)
│   ├── usuario.py        # Clase base abstracta Usuario
│   ├── usuario_final.py  # UsuarioFinal + enum Claustro
│   ├── usuario_admin.py  # UsuarioAdmin + enum RolAdmin
│   ├── reclamo.py        # Modelo Reclamo + enum EstadoReclamo
│   ├── departamento.py   # Modelo Departamento
│   ├── clasificador.py   # Wrapper del clasificador (pickle)
│   ├── similitud.py      # Búsqueda de reclamos similares
│   ├── generador_reportes.py   # Reportes HTML/PDF (patrón Factory)
│   └── ...
├── templates/            # Plantillas Jinja2
├── tests/                # Tests unitarios (unittest)
├── docs/                 # Documentación y diagramas UML
├── data/                 # Modelo ML pre-entrenado (claims_clf.pkl)
├── server.py             # Punto de entrada
├── init_db.py            # Inicialización de BD
└── seed_db.py            # Datos de prueba
```

---

## Tecnologías

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **ML:** scikit-learn (clasificador provisto por cátedra)
- **Visualización:** matplotlib, wordcloud
- **PDF:** xhtml2pdf
- **Testing:** unittest
