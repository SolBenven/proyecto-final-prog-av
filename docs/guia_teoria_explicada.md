# Guía de Teoría Explicada con Ejemplos del TP
## Sistema de Gestión de Reclamos - Facultad de Ingeniería UNER

Este documento explica cada concepto teórico de la materia usando ejemplos directos del código del trabajo práctico. Para cada tema se indica la ubicación exacta en el código fuente.

---

## UNIDAD 1: Programación Orientada a Objetos

### 1.1 Clases y Objetos

**Definición:** Una clase es un molde que define atributos y métodos. Un objeto es una instancia concreta de esa clase.

**Ejemplo en el TP:**
```python
# modules/reclamo.py
class Reclamo(db.Model):
    """Clase que define la estructura y comportamiento de un reclamo"""
    __tablename__ = "reclamo"

    id: Mapped[int] = mapped_column(primary_key=True)
    detalle: Mapped[str] = mapped_column(nullable=False)
    estado: Mapped[EstadoReclamo] = mapped_column(default=EstadoReclamo.PENDIENTE)
    ruta_imagen: Mapped[str | None] = mapped_column(nullable=True)
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)
    actualizado_en: Mapped[Datetime] = mapped_column(default=Datetime.now, onupdate=Datetime.now)

    # Claves Foráneas
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    creador_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))

# Crear un objeto (instancia):
reclamo = Reclamo(
    detalle="Se rompió la ventana del aula 102",
    departamento_id=1,
    creador_id=5,
)
```

### 1.2 Encapsulamiento

**Definición:** Ocultar los detalles internos de una clase y exponer solo una interfaz pública controlada.

**Ejemplo en el TP:**
```python
# modules/usuario.py
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    hash_contrasena: Mapped[str] = mapped_column(nullable=False)  # Encapsulado

    def establecer_contrasena(self, contrasena: str):
        """Interfaz pública para establecer contraseña"""
        self.hash_contrasena = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena: str) -> bool:
        """Interfaz pública para verificar contraseña"""
        return check_password_hash(self.hash_contrasena, contrasena)
```

**Ventaja:** Si cambio el algoritmo de hash (bcrypt → argon2), solo modifico estos dos métodos.

### 1.3 Herencia

**Definición:** Un mecanismo que permite que una clase derive de otra, reutilizando atributos y métodos.

**Ejemplo en el TP (Single Table Inheritance):**
```python
# modules/usuario.py
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """Clase base abstracta — define atributos y métodos comunes"""
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str]
    apellido: Mapped[str]
    correo: Mapped[str]
    nombre_usuario: Mapped[str]
    hash_contrasena: Mapped[str]
    tipo_usuario: Mapped[str]  # Discriminador

    __mapper_args__ = {"polymorphic_on": tipo_usuario}

    def establecer_contrasena(self, contrasena: str): ...
    def verificar_contrasena(self, contrasena: str) -> bool: ...

    @property
    @abstractmethod
    def nombre_completo(self) -> str: ...

# modules/usuario_final.py
class UsuarioFinal(Usuario):
    """Hereda de Usuario — agrega claustro"""
    claustro: Mapped[Claustro | None]
    __mapper_args__ = {"polymorphic_identity": "usuario_final"}

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    """Hereda de Usuario — agrega rol y departamento"""
    departamento_id: Mapped[int | None]
    rol_admin: Mapped[RolAdmin | None]
    __mapper_args__ = {"polymorphic_identity": "usuario_admin"}
```

**Ventaja:** No se duplica código de autenticación en cada tipo de usuario.

### 1.4 Polimorfismo

**Definición:** La capacidad de diferentes objetos de responder al mismo mensaje de manera distinta.

**Ejemplo en el TP:**
```python
# modules/usuario.py — Método abstracto
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    @property
    @abstractmethod
    def nombre_completo(self) -> str:
        pass

# modules/usuario_final.py — Implementación 1
class UsuarioFinal(Usuario):
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.claustro.value}"
        # → "Juan Pérez - estudiante"

# modules/usuario_admin.py — Implementación 2
class UsuarioAdmin(Usuario):
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.rol_admin.value}"
        # → "Ana López - jefe_departamento"

# Uso polimórfico en modules/rutas.py:
@login_manager.user_loader
def cargar_usuario(usuario_id):
    return Usuario.obtener_por_id(int(usuario_id))
    # Retorna UsuarioFinal o UsuarioAdmin según tipo_usuario
    # current_user.nombre_completo → llama al método correcto
```

### 1.5 Clases Abstractas y ABC

**Definición:** Una clase abstracta no puede instanciarse directamente y define métodos que las subclases deben implementar.

**Ejemplo en el TP — Metaclase combinada:**
```python
# modules/usuario.py
from abc import ABC, ABCMeta, abstractmethod

class MetaModeloABC(ABCMeta, type(db.Model)):
    """Metaclase combinada: permite usar ABC con SQLAlchemy Model."""
    pass

class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """No se puede instanciar directamente — nombre_completo es abstracto"""

    @property
    @abstractmethod
    def nombre_completo(self) -> str:
        pass

# Esto lanzaría TypeError:
# usuario = Usuario(...)  # ✗ No se puede instanciar clase abstracta
```

**Ejemplo en el TP — ABC para Reportes:**
```python
# modules/generador_reportes.py
from abc import ABC, abstractmethod

class Reporte(ABC):
    """Clase base abstracta para generación de reportes"""

    def __init__(self, departamento_ids: list[int], es_secretario_tecnico: bool = False):
        self.departamento_ids = departamento_ids
        self.es_secretario_tecnico = es_secretario_tecnico

    @abstractmethod
    def generar(self) -> str | bytes | None:
        pass

class ReporteHTML(Reporte):
    def generar(self) -> str: ...

class ReportePDF(Reporte):
    def generar(self) -> bytes | None: ...

# Factory function
def crear_reporte(formato_reporte: str, departamento_ids, es_secretario_tecnico) -> Reporte:
    if formato_reporte == "pdf":
        return ReportePDF(departamento_ids, es_secretario_tecnico)
    return ReporteHTML(departamento_ids, es_secretario_tecnico)
```

---

## UNIDAD 2: Relaciones entre Objetos

### 2.1 Composición

**Definición:** Relación "tiene un" donde la parte no puede existir sin el todo. Si se elimina el todo, se eliminan sus partes.

**Ejemplo en el TP:**
```python
# modules/reclamo.py
class Reclamo(db.Model):
    # COMPOSICIÓN: estas entidades no existen sin el reclamo
    adherentes: Mapped[list["AdherenteReclamo"]] = relationship(
        "AdherenteReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← Si elimino Reclamo, elimino adherentes
    )
    historial_estados: Mapped[list["HistorialEstadoReclamo"]] = relationship(
        "HistorialEstadoReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← Si elimino Reclamo, elimino historial
    )
    derivaciones: Mapped[list["DerivacionReclamo"]] = relationship(
        "DerivacionReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← Si elimino Reclamo, elimino derivaciones
    )
```

### 2.2 Agregación

**Definición:** Relación "tiene un" donde las partes existen independientemente del todo.

**Ejemplo en el TP:**
```python
# modules/reclamo.py
class Reclamo(db.Model):
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
    departamento: Mapped["Departamento"] = relationship(...)
    # AGREGACIÓN: si elimino el reclamo, el departamento sigue existiendo

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamento.id"), nullable=True,
    )
    # AGREGACIÓN: si elimino el admin, el departamento sigue existiendo
```

### 2.3 Asociación Muchos a Muchos (N:M)

**Definición:** Ambos lados de la relación existen independientemente. Se modela con una tabla intermedia.

**Ejemplo en el TP:**
```python
# modules/adherente_reclamo.py
class AdherenteReclamo(db.Model):
    """Tabla intermedia para relación N:M (UsuarioFinal ↔ Reclamo)"""
    __tablename__ = "adherente_reclamo"

    id: Mapped[int] = mapped_column(primary_key=True)
    reclamo_id: Mapped[int] = mapped_column(ForeignKey("reclamo.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

    __table_args__ = (UniqueConstraint("reclamo_id", "usuario_id"),)
    # ↑ Un usuario solo puede adherirse una vez al mismo reclamo
```

### 2.4 Dependencia

**Definición:** Una clase usa otra temporalmente sin almacenarla como atributo.

**Ejemplo en el TP:**
```python
# modules/reclamo.py
from modules.clasificador import clasificador

class Reclamo(db.Model):
    @staticmethod
    def _clasificar_departamento(detalle: str) -> int | None:
        """DEPENDE de clasificador pero NO lo almacena"""
        try:
            nombre_predicho = clasificador.clasificar(detalle)
            depto = Departamento.obtener_por_nombre(nombre_predicho)
            return depto.id if depto else None
        except Exception:
            return None
```

---

## UNIDAD 3: Pruebas Unitarias

### 3.1 Patrón AAA (Arrange-Act-Assert)

**Definición:** Patrón para organizar pruebas en tres secciones claras: preparar, ejecutar, verificar.

**Ejemplo en el TP:**
```python
# tests/test_reclamo.py
import unittest
from modules.config import db
from modules.reclamo import Reclamo, EstadoReclamo
from modules.usuario_final import UsuarioFinal, Claustro
from tests.conftest import CasoTestBase


class TestReclamo(CasoTestBase):
    def setUp(self):
        super().setUp()
        self.usuario = UsuarioFinal(
            nombre="Test", apellido="User",
            correo="test@test.com", nombre_usuario="testuser",
            claustro=Claustro.ESTUDIANTE,
        )
        self.usuario.establecer_contrasena("test123")
        db.session.add(self.usuario)
        db.session.commit()

    def test_crear_reclamo_con_departamento(self):
        # ==================== ARRANGE ====================
        detalle = "Se rompió la ventana del aula 102"
        depto_id = self.depto1_id
        usuario_id = self.usuario.id

        # ==================== ACT ====================
        reclamo, error = Reclamo.crear(
            creador_id=usuario_id, detalle=detalle, departamento_id=depto_id,
        )

        # ==================== ASSERT ====================
        self.assertIsNotNone(reclamo)
        self.assertIsNone(error)
        self.assertEqual(reclamo.detalle, detalle)
        self.assertEqual(reclamo.departamento_id, depto_id)
        self.assertEqual(reclamo.estado, EstadoReclamo.PENDIENTE)
        self.assertEqual(reclamo.creador_id, usuario_id)
```

### 3.2 Clase Base de Tests

```python
# tests/conftest.py
import unittest
from modules.config import create_app, db


class CasoTestBase(unittest.TestCase):
    """Clase base para todas las pruebas. Configura y limpia la BD."""

    def setUp(self):
        self.app = create_app()
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self._crear_departamentos_prueba()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _crear_departamentos_prueba(self):
        """Crea departamentos de prueba: secretaria_tecnica, ciencias, humanidades."""
        from modules.departamento import Departamento
        st = Departamento(nombre="secretaria_tecnica", nombre_mostrar="Secretaría Técnica",
                          es_secretaria_tecnica=True)
        d1 = Departamento(nombre="ciencias", nombre_mostrar="Ciencias")
        d2 = Departamento(nombre="humanidades", nombre_mostrar="Humanidades")
        db.session.add_all([st, d1, d2])
        db.session.commit()
        self.st_id = st.id
        self.depto1_id = d1.id
        self.depto2_id = d2.id
```

### 3.3 Archivos de Tests

| Archivo | Qué testea |
|---------|------------|
| `tests/test_reclamo.py` | Creación, estado, consultas de reclamos |
| `tests/test_usuario.py` | Registro, autenticación, validaciones |
| `tests/test_adherente_reclamo.py` | Adhesión, duplicados, quitar adhesión |
| `tests/test_departamento.py` | CRUD de departamentos |
| `tests/test_clasificador_unit.py` | Clasificador ML unitario |
| `tests/test_similitud_unit.py` | Búsqueda de similitud |
| `tests/test_notificacion.py` | Notificaciones y marcado como leídas |
| `tests/test_derivacion_reclamo.py` | Derivación de reclamos |
| `tests/test_manejador_imagen.py` | Validación y guardado de imágenes |
| `tests/test_admin_y_reportes.py` | Panel admin y generación de reportes |
| `tests/test_analiticas.py` | Estadísticas y gráficos |

---

## UNIDAD 4: Principios SOLID

### S - Single Responsibility Principle (SRP)

Cada clase tiene una única responsabilidad.

**Ejemplo en el TP:**
```python
# Cada módulo tiene UNA responsabilidad:
# modules/reclamo.py         → Gestionar reclamos
# modules/clasificador.py    → Clasificar texto con ML
# modules/similitud.py       → Buscar reclamos similares
# modules/manejador_imagen.py → Gestionar imágenes
# modules/generador_analiticas.py → Generar estadísticas y gráficos
# modules/generador_reportes.py   → Generar reportes HTML/PDF
# modules/notificacion_usuario.py → Gestionar notificaciones
```

### O - Open/Closed Principle

Abierto a extensión, cerrado a modificación.

**Ejemplo en el TP:**
```python
# modules/generador_reportes.py
class Reporte(ABC):
    @abstractmethod
    def generar(self) -> str | bytes | None:
        pass

class ReporteHTML(Reporte):
    def generar(self) -> str: ...

class ReportePDF(Reporte):
    def generar(self) -> bytes | None: ...

# Si quiero agregar ReporteCSV, creo una nueva clase sin modificar las existentes:
# class ReporteCSV(Reporte):
#     def generar(self) -> str: ...
```

### L - Liskov Substitution Principle

Los subtipos deben poder sustituir a sus supertipos sin romper el programa.

**Ejemplo en el TP:**
```python
# modules/usuario.py, usuario_final.py, usuario_admin.py
# UsuarioFinal y UsuarioAdmin pueden usarse donde se espera Usuario:

@login_manager.user_loader
def cargar_usuario(usuario_id):
    return Usuario.obtener_por_id(int(usuario_id))
    # Retorna UsuarioFinal o UsuarioAdmin — ambos funcionan como Usuario

# current_user.nombre_completo funciona correctamente
# sin importar si es UsuarioFinal o UsuarioAdmin
```

### I - Interface Segregation Principle

Cada subclase solo tiene lo que necesita.

**Ejemplo en el TP:**
```python
# modules/usuario_final.py
class UsuarioFinal(Usuario):
    """Solo tiene lo que necesita un usuario final"""
    claustro: Mapped[Claustro | None]
    # NO tiene métodos de administración

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    """Solo tiene lo que necesita un administrador"""
    departamento_id: Mapped[int | None]
    rol_admin: Mapped[RolAdmin | None]

    @property
    def es_jefe_departamento(self) -> bool: ...

    @property
    def es_secretario_tecnico(self) -> bool: ...

    def puede_acceder_reclamo(self, reclamo) -> bool: ...
    # NO tiene claustro (no pertenece a un claustro)
```

### D - Dependency Inversion Principle

Depender de abstracciones, no de implementaciones concretas.

**Ejemplo en el TP:**
```python
# modules/reclamo.py
class Reclamo(db.Model):
    @staticmethod
    def crear(creador_id, detalle, departamento_id=None, ruta_imagen=None):
        # DEPENDE de la abstracción db, no de una implementación concreta
        db.session.add(reclamo)  # ← db podría ser SQLite, PostgreSQL, MySQL
        db.session.commit()

        # DEPENDE de la abstracción del clasificador
        nombre_predicho = clasificador.clasificar(detalle)
        # ← No sabe si usa TF-IDF, redes neuronales, o reglas simples

# Si cambiamos la base de datos de SQLite a PostgreSQL,
# Reclamo NO cambia (depende de la abstracción db.Model)

# Si cambiamos el algoritmo de clasificación de TF-IDF a BERT,
# Reclamo NO cambia (depende de la interfaz clasificador.clasificar())
```

---

## UNIDAD 5: Manejo de Excepciones

### 5.1 Tipos de Errores

**Errores de Sintaxis:**
```python
# Esto no ejecuta:
if x == 5
    print("cinco")  # ✗ Falta :
```

**Excepciones (errores en tiempo de ejecución):**
```python
# Esto ejecuta pero puede fallar:
def dividir(a, b):
    return a / b  # ✗ ZeroDivisionError si b=0
```

### 5.2 Gestión de Excepciones en el TP

**Ejemplo básico:**
```python
# modules/reclamo.py
class Reclamo(db.Model):
    @staticmethod
    def _clasificar_departamento(detalle: str) -> int | None:
        try:
            # INTENTAR clasificar
            nombre_predicho = clasificador.clasificar(detalle)
            depto = Departamento.obtener_por_nombre(nombre_predicho)
            return depto.id if depto else None

        except Exception as e:
            # CAPTURAR cualquier error
            print(f"Error en clasificación: {e}")
            return None  # Retornar valor por defecto
```

**Ejemplo con IntegrityError:**
```python
# modules/reclamo.py
@staticmethod
def agregar_adherente(reclamo_id: int, usuario_id: int) -> tuple[bool, str | None]:
    try:
        reclamo = db.session.get(Reclamo, reclamo_id)
        if not reclamo:
            return False, "Reclamo no encontrado"

        adherente = AdherenteReclamo(reclamo_id=reclamo_id, usuario_id=usuario_id)
        db.session.add(adherente)
        db.session.commit()
        return True, None

    except IntegrityError:
        # Error de integridad (usuario ya adherido — UniqueConstraint)
        db.session.rollback()
        return False, "Ya estás adherido a este reclamo"

    except Exception as e:
        db.session.rollback()
        return False, f"Error inesperado: {str(e)}"
```

### 5.3 Garantías de Seguridad

**Garantía Básica:** Si hay error, el sistema queda en un estado válido.

```python
# modules/reclamo.py
@staticmethod
def actualizar_estado(reclamo_id, nuevo_estado, cambiado_por_id):
    try:
        reclamo = db.session.get(Reclamo, reclamo_id)
        reclamo.estado = nuevo_estado

        historial = HistorialEstadoReclamo(...)
        db.session.add(historial)
        db.session.commit()
        return reclamo, None
    except Exception as e:
        db.session.rollback()  # ← GARANTÍA BÁSICA: estado válido
        return None, f"Error: {e}"
```

**Garantía Fuerte:** O completa con éxito O deja todo como estaba.

```python
# modules/derivacion_reclamo.py
@staticmethod
def derivar(reclamo_id, departamento_destino_id, derivado_por_id, motivo=None):
    try:
        # Cambiar departamento
        reclamo.departamento_id = departamento_destino_id

        # Crear registro de derivación
        derivacion = DerivacionReclamo(...)
        db.session.add(derivacion)

        db.session.commit()  # ← TODO o NADA
        return True, None
    except Exception as e:
        db.session.rollback()  # ← Vuelve al estado inicial
        return False, f"Error: {e}"
```

---

## UNIDAD 6: Biblioteca Estándar y Módulos

### 6.1 Uso de Módulos Estándar

```python
# Módulo os (sistema operativo)
import os
# modules/manejador_imagen.py
CARPETA_SUBIDA = os.path.join("static", "uploads", "claims")

# Módulo datetime
from datetime import datetime as Datetime
# modules/reclamo.py
creado_en: Mapped[Datetime] = mapped_column(default=Datetime.now)

# Módulo enum
from enum import Enum
# modules/reclamo.py
class EstadoReclamo(Enum):
    INVALIDO = "Inválido"
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En proceso"
    RESUELTO = "Resuelto"

# Módulo abc
from abc import ABC, ABCMeta, abstractmethod
# modules/usuario.py
class MetaModeloABC(ABCMeta, type(db.Model)): ...
```

### 6.2 Módulos de PyPI (Python Package Index)

```python
# requirements.txt — Módulos instalados desde PyPI
Flask                 # Framework web
Flask-Login           # Autenticación
Flask-SQLAlchemy      # ORM
scikit-learn          # Machine Learning
Pillow                # Procesamiento de imágenes
matplotlib            # Gráficos
wordcloud             # Nube de palabras
xhtml2pdf             # Generación de PDF
joblib                # Persistencia de modelos ML

# Uso en el código:
from flask import Flask, request, render_template       # PyPI
from flask_login import login_required, current_user     # PyPI
from sklearn.feature_extraction.text import TfidfVectorizer  # PyPI
from PIL import Image                                    # PyPI (Pillow)
```

---

## UNIDAD 7: Protocolo de Iteradores en Python

### 7.1 ¿Qué es el Protocolo de Iteradores?

El protocolo de iteradores en Python permite recorrer elementos de una colección secuencialmente sin exponer su estructura interna. Se basa en dos métodos:
- `__iter__()`: Retorna el iterador (debe retornar `self` o un objeto iterador)
- `__next__()`: Retorna el siguiente elemento, o lanza `StopIteration` cuando no hay más

**Ejemplo conceptual:**
```python
class MiIterador:
    def __init__(self, datos):
        self.datos = datos
        self.indice = 0

    def __iter__(self):
        """Retorna el iterador (self)"""
        return self

    def __next__(self):
        """Retorna el siguiente elemento"""
        if self.indice < len(self.datos):
            resultado = self.datos[self.indice]
            self.indice += 1
            return resultado
        else:
            raise StopIteration

# Uso:
mi_iter = MiIterador([1, 2, 3, 4, 5])
for numero in mi_iter:
    print(numero)  # Imprime 1, 2, 3, 4, 5
```

**¿Cómo funciona el for loop internamente?**
```python
# Este código:
for item in coleccion:
    print(item)

# Es equivalente a:
iterador = iter(coleccion)  # Llama a coleccion.__iter__()
while True:
    try:
        item = next(iterador)  # Llama a iterador.__next__()
        print(item)
    except StopIteration:
        break
```

### 7.2 Ejemplo Aplicado al TP — Iterador de Reclamos por Estado

```python
# Ejemplo hipotético aplicable al TP
class IteradorReclamosPorEstado:
    """Iterador que recorre reclamos de un estado específico de forma lazy."""
    def __init__(self, estado: EstadoReclamo):
        self.estado = estado
        self.query = Reclamo.query.filter_by(estado=estado)
        self.offset = 0
        self.batch_size = 10
        self.batch_actual = []
        self.indice_batch = 0

    def __iter__(self):
        return self

    def __next__(self) -> Reclamo:
        if self.indice_batch >= len(self.batch_actual):
            self.batch_actual = (
                self.query.offset(self.offset).limit(self.batch_size).all()
            )
            self.offset += self.batch_size
            self.indice_batch = 0
            if not self.batch_actual:
                raise StopIteration

        reclamo = self.batch_actual[self.indice_batch]
        self.indice_batch += 1
        return reclamo

# Uso:
pendientes = IteradorReclamosPorEstado(EstadoReclamo.PENDIENTE)
for reclamo in pendientes:
    print(f"Reclamo #{reclamo.id}: {reclamo.detalle}")
```

### 7.3 Generadores con yield

```python
# Ejemplo hipotético aplicable al TP
class Reclamo(db.Model):
    @staticmethod
    def iterar_por_departamento(departamento_id: int):
        """Generador que itera sobre reclamos de un departamento."""
        offset = 0
        batch_size = 50
        while True:
            reclamos = (
                Reclamo.query
                .filter_by(departamento_id=departamento_id)
                .offset(offset).limit(batch_size).all()
            )
            if not reclamos:
                break
            for reclamo in reclamos:
                yield reclamo
            offset += batch_size

# Uso:
for reclamo in Reclamo.iterar_por_departamento(departamento_id=1):
    print(reclamo.detalle)
```

### 7.4 Objetos Iterables en el TP

```python
# modules/reclamo.py
class Reclamo(db.Model):
    # Estas relaciones son ITERABLES (tienen __iter__)
    adherentes: Mapped[list["AdherenteReclamo"]] = relationship(...)
    historial_estados: Mapped[list["HistorialEstadoReclamo"]] = relationship(...)

# Uso — Se pueden iterar directamente:
reclamo = Reclamo.obtener_por_id(1)

for adherente in reclamo.adherentes:  # ← Implementa __iter__
    print(adherente.usuario.nombre_completo)

for historial in reclamo.historial_estados:
    print(f"{historial.cambiado_en}: {historial.estado_anterior} → {historial.estado_nuevo}")

# Comprehensions (usan el protocolo de iteración):
conteo_pendientes = len([r for r in reclamos if r.estado == EstadoReclamo.PENDIENTE])
total_adherentes = sum(r.cantidad_adherentes for r in reclamos)
```

---

## UNIDAD 8: Algoritmos de Machine Learning

### 8.1 Clasificación con Machine Learning

> **Importante:** El clasificador utiliza un **modelo pre-entrenado provisto por la cátedra** (`data/claims_clf.pkl`). **No se entrena localmente.**

```python
# modules/clasificador.py
"""
Clasificador automático de reclamos usando pickle + ClaimsClassifier.
"""
import os
import pickle


class Clasificador:
    """
    Wrapper del clasificador provisto por la cátedra.
    Carga el modelo desde data/claims_clf.pkl y expone el método clasificar().
    """

    RUTA_MODELO = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "claims_clf.pkl")

    def __init__(self):
        self.__clf = None
        if os.path.exists(self.RUTA_MODELO):
            with open(self.RUTA_MODELO, "rb") as archivo:
                self.__clf = pickle.load(archivo)

    def clasificar(self, texto: str) -> str:
        """Clasifica un texto y devuelve el nombre de departamento interno."""
        resultado = self.__clf.classify([texto])[0]
        # Tabla de mapeo: etiqueta del modelo → nombre interno de departamento
        tabla = {
            "soporte informático": "Secretario Informartico - secretario_informatico",
            "secretaría técnica": "Secretario Técnico - secretario_tecnico",
            "maestranza": "Maestranza - maestranza",
        }
        return tabla[resultado]

    def modelo_disponible(self) -> bool:
        """Retorna True si el modelo fue cargado correctamente."""
        return self.__clf is not None


# Instancia global
clasificador = Clasificador()
```

### 8.2 Uso del Clasificador

El clasificador se utiliza automáticamente al crear un reclamo:

```python
# modules/reclamo.py
@staticmethod
def _clasificar_departamento(detalle: str) -> int | None:
    """Usa el Clasificador ML para predecir el departamento."""
    try:
        nombre_predicho = clasificador.clasificar(detalle)
        depto = Departamento.obtener_por_nombre(nombre_predicho)
        return depto.id if depto else None
    except Exception:
        return None
```

### 8.3 Similitud de Textos

```python
# modules/similitud.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BuscadorSimilitud:
    """Busca reclamos similares usando TF-IDF y similitud del coseno."""

    def buscar_reclamos_similares(
        self, texto: str,
        departamento_id: int | None = None,
        umbral: float = 0.25,
        limite: int = 5,
        excluir_reclamo_id: int | None = None,
    ) -> list:
        """
        Encuentra reclamos similares al texto dado.
        Solo busca entre reclamos PENDIENTES.
        Umbral por defecto: 0.25
        """
        reclamos = Reclamo.obtener_pendientes()
        # ... vectorizar, calcular similitud del coseno, filtrar ...
        return reclamos_similares


# Instancia global
buscador_similitud = BuscadorSimilitud()
```

---

## Resumen de Conceptos Clave por Ubicación en el TP

### Herencia (Single Table Inheritance)
- **Ubicación:** `modules/usuario.py`, `modules/usuario_final.py`, `modules/usuario_admin.py`
- **Concepto:** Usuario → UsuarioFinal, UsuarioAdmin

### Clases Abstractas (ABC)
- **Ubicación:** `modules/usuario.py` (MetaModeloABC), `modules/generador_reportes.py` (Reporte)
- **Concepto:** Usuario con `nombre_completo` abstracto, Reporte con `generar()` abstracto

### Composición
- **Ubicación:** `modules/reclamo.py`
- **Concepto:** `cascade="all, delete-orphan"` en relaciones con adherentes, historial, derivaciones

### Agregación
- **Ubicación:** `modules/usuario_admin.py`, `modules/reclamo.py`
- **Concepto:** UsuarioAdmin → Departamento, Reclamo → Departamento

### Asociación (Many-to-Many)
- **Ubicación:** `modules/adherente_reclamo.py`
- **Concepto:** UsuarioFinal ↔ Reclamo

### Encapsulamiento
- **Ubicación:** `modules/usuario.py`
- **Concepto:** `hash_contrasena` con `establecer_contrasena()`, `verificar_contrasena()`

### Properties
- **Ubicación:** `modules/reclamo.py`, `modules/usuario_admin.py`
- **Concepto:** `@property cantidad_adherentes`, `@property es_jefe_departamento`

### Polimorfismo
- **Ubicación:** `modules/usuario.py`, `modules/usuario_final.py`, `modules/usuario_admin.py`
- **Concepto:** `nombre_completo` diferente en UsuarioFinal y UsuarioAdmin

### Decoradores
- **Ubicación:** `modules/utils/decoradores.py`
- **Concepto:** `@admin_requerido`, `@usuario_final_requerido`, `@rol_admin_requerido`

### Excepciones
- **Ubicación:** `modules/reclamo.py`, `modules/derivacion_reclamo.py`
- **Concepto:** try-except con IntegrityError, rollback de transacciones

### Pruebas Unitarias (AAA)
- **Ubicación:** `tests/`
- **Concepto:** Arrange-Act-Assert, `CasoTestBase`, `unittest`

### Principio de Responsabilidad Única
- **Ubicación:** `modules/`
- **Concepto:** Cada módulo tiene UNA responsabilidad

### Persistencia
- **Ubicación:** Todos los modelos, `db.session.add()`, `db.session.commit()`
- **Concepto:** SQLAlchemy ORM con Single Table Inheritance

### Clasificación/ML
- **Ubicación:** `modules/clasificador.py`
- **Concepto:** Modelo pre-entrenado provisto por cátedra (`data/claims_clf.pkl`)

### Similitud
- **Ubicación:** `modules/similitud.py`
- **Concepto:** TF-IDF + Cosine Similarity, umbral 0.25, solo reclamos PENDIENTES

---

## Consejos para el Examen Teórico

### Para preguntas conceptuales:
1. **Lee teoria.md** (documento de teoría pura)
2. **Identifica el concepto** en el enunciado
3. **Relaciona con tu código** mental usando los ejemplos de aquí

### Para preguntas de "dé un ejemplo":
1. Usa los ejemplos de este documento
2. Menciona la ubicación en tu código (ej: "En modules/reclamo.py...")
3. Explica BREVEMENTE qué hace

### Para la defensa escrita:
1. Ten las ubicaciones memorizadas
2. Practica explicar cada concepto en 2-3 oraciones
3. Usa los nombres reales del código (en español)

---

**Fin del documento de teoría explicada**
