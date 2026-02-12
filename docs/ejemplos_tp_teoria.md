# Defensa Escrita del TP - Sistema de Gestión de Reclamos
## Respuestas a Preguntas Teóricas con Ejemplos de Código

---

## PREGUNTA 1: Problema que resuelve el programa y uso de OO

### ¿Qué problema resuelve el programa desarrollado?

El sistema de gestión de reclamos desarrollado resuelve el problema de **gestionar y dar seguimiento a los reclamos universitarios** de forma organizada y eficiente.

**Problemas específicos que aborda:**

1. **Desorganización en la recepción de reclamos:** Los reclamos llegan por múltiples canales sin un sistema centralizado
2. **Asignación manual a departamentos:** Se requiere personal para clasificar cada reclamo
3. **Falta de seguimiento:** Los usuarios no saben el estado de sus reclamos
4. **Duplicación de esfuerzos:** No se detectan reclamos similares
5. **Falta de métricas:** No hay datos sobre tipos de problemas ni estadísticas

**Soluciones implementadas:**

- **Centralización:** Un único sistema web para crear y consultar reclamos
- **Clasificación automática:** Modelo ML provisto por la cátedra clasifica reclamos por departamento
- **Seguimiento en tiempo real:** Sistema de notificaciones cuando cambia el estado
- **Detección de similitud:** TF-IDF + similitud del coseno para encontrar reclamos relacionados
- **Analytics:** Dashboards con estadísticas, gráficos y reportes PDF

---

### Importancia del uso de la Orientación a Objetos

La orientación a objetos es fundamental en este proyecto por las siguientes razones:

#### 1. **Modelado Natural del Dominio**

```python
# modules/reclamo.py
class Reclamo(db.Model):
    """Un reclamo es una entidad del mundo real"""
    detalle: Mapped[str]
    estado: Mapped[EstadoReclamo]
    departamento: Mapped["Departamento"]
    creador: Mapped["UsuarioFinal"]
```

Esto permite **pensar en el problema en términos del dominio** (reclamos, usuarios, departamentos).

#### 2. **Encapsulamiento de Responsabilidades**

```python
# modules/usuario.py
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    hash_contrasena: Mapped[str]  # Encapsulado — no se accede directamente

    def establecer_contrasena(self, contrasena: str):
        """Interfaz pública para establecer contraseña"""
        self.hash_contrasena = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena: str) -> bool:
        """Interfaz pública para verificar contraseña"""
        return check_password_hash(self.hash_contrasena, contrasena)
```

**Ventaja:** Si cambio el algoritmo de hash, solo modifico estos dos métodos.

#### 3. **Herencia para Reutilización de Código**

```python
# modules/usuario.py — Clase base abstracta con MetaModeloABC
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """Funcionalidad común: autenticación, datos personales"""
    nombre: Mapped[str]
    apellido: Mapped[str]
    correo: Mapped[str]
    nombre_usuario: Mapped[str]
    def establecer_contrasena(self, contrasena): ...
    def verificar_contrasena(self, contrasena) -> bool: ...

# modules/usuario_final.py
class UsuarioFinal(Usuario):
    """Hereda autenticación + agrega claustro"""
    claustro: Mapped[Claustro | None]

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    """Hereda autenticación + agrega rol y departamento"""
    rol_admin: Mapped[RolAdmin | None]
    departamento_id: Mapped[int | None]
```

**Ventaja:** No duplico código de autenticación en cada tipo de usuario.

#### 4. **Polimorfismo para Flexibilidad**

```python
# modules/usuario.py — Método abstracto
class Usuario(...):
    @property
    @abstractmethod
    def nombre_completo(self) -> str:
        pass

# modules/usuario_final.py
class UsuarioFinal(Usuario):
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.claustro.value}"

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.rol_admin.value}"

# Uso polimórfico:
usuarios: list[Usuario] = [UsuarioFinal(...), UsuarioAdmin(...)]
for usuario in usuarios:
    print(usuario.nombre_completo)  # Cada uno responde diferente
```

#### 5. **Modularidad y Mantenibilidad**

```
modules/
├── config.py                # Fábrica de aplicación, db, login_manager
├── rutas.py                 # Todas las rutas consolidadas (sin blueprints)
├── usuario.py               # Usuario base abstracto + MetaModeloABC
├── usuario_final.py         # UsuarioFinal + Claustro enum
├── usuario_admin.py         # UsuarioAdmin + RolAdmin enum
├── reclamo.py               # Reclamos con métodos estáticos
├── departamento.py          # Departamentos
├── clasificador.py          # Clasificador ML
├── similitud.py             # BuscadorSimilitud
└── utils/                   # Utilidades compartidas
```

#### 6. **Composición para Relaciones Complejas**

```python
# modules/reclamo.py
class Reclamo(db.Model):
    """Reclamo está COMPUESTO por otras entidades"""
    historial_estados: Mapped[list["HistorialEstadoReclamo"]] = relationship(
        cascade="all, delete-orphan",  # Si elimino Reclamo, elimino su historial
    )
    adherentes: Mapped[list["AdherenteReclamo"]] = relationship(
        cascade="all, delete-orphan",
    )
    derivaciones: Mapped[list["DerivacionReclamo"]] = relationship(
        cascade="all, delete-orphan",
    )
```

---

## PREGUNTA 2: Relaciones entre objetos en el diagrama de clases

### Fundamente la elección de las relaciones

En el diagrama de clases (`docs/class.puml`) implementé diferentes tipos de relaciones según las necesidades del negocio:

---

#### HERENCIA: Usuario → UsuarioFinal, UsuarioAdmin

**Ubicación:** `modules/usuario.py`, `modules/usuario_final.py`, `modules/usuario_admin.py`

```python
class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """Clase base abstracta — usa MetaModeloABC para resolver conflicto de metaclases"""
    __tablename__ = "usuario"
    tipo_usuario: Mapped[str]  # Discriminador
    __mapper_args__ = {"polymorphic_on": tipo_usuario}

class UsuarioFinal(Usuario):
    __mapper_args__ = {"polymorphic_identity": "usuario_final"}

class UsuarioAdmin(Usuario):
    __mapper_args__ = {"polymorphic_identity": "usuario_admin"}
```

**Justificación:**
- Relación "es un(a)": UsuarioFinal **ES UN** Usuario, UsuarioAdmin **ES UN** Usuario
- Comparten atributos comunes (correo, nombre_usuario, hash_contrasena)
- Comparten comportamiento común (autenticación: `establecer_contrasena()`, `verificar_contrasena()`)
- Cada uno agrega comportamiento específico e implementa `nombre_completo`
- Single Table Inheritance para eficiencia en consultas

**UML:** `Usuario <|-- UsuarioFinal` y `Usuario <|-- UsuarioAdmin`

---

#### COMPOSICIÓN: Reclamo → HistorialEstadoReclamo, AdherenteReclamo, DerivacionReclamo

**Ubicación:** `modules/reclamo.py`

```python
class Reclamo(db.Model):
    historial_estados: Mapped[list["HistorialEstadoReclamo"]] = relationship(
        "HistorialEstadoReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← COMPOSICIÓN
    )
    adherentes: Mapped[list["AdherenteReclamo"]] = relationship(
        "AdherenteReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← COMPOSICIÓN
    )
    derivaciones: Mapped[list["DerivacionReclamo"]] = relationship(
        "DerivacionReclamo", back_populates="reclamo",
        cascade="all, delete-orphan",  # ← COMPOSICIÓN
    )
```

**Justificación:**
- El historial de estados **NO EXISTE** sin el reclamo
- Los adherentes de un reclamo **NO TIENEN SENTIDO** sin el reclamo
- Las derivaciones **PERTENECEN EXCLUSIVAMENTE** a un reclamo
- Al eliminar un Reclamo, deben eliminarse sus partes (`cascade="all, delete-orphan"`)
- Relación todo-parte con ciclo de vida dependiente

**UML:** `Reclamo "1" *--> "*" HistorialEstadoReclamo` (rombo relleno)

---

#### AGREGACIÓN: UsuarioAdmin → Departamento, Reclamo → Departamento

**Ubicación:** `modules/usuario_admin.py`, `modules/reclamo.py`

```python
# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    departamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("departamento.id"), nullable=True,
    )

# modules/reclamo.py
class Reclamo(db.Model):
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"))
```

**Justificación:**
- Un UsuarioAdmin **PERTENECE A** un Departamento
- El Departamento **EXISTE INDEPENDIENTEMENTE** del UsuarioAdmin o del Reclamo
- Si elimino un admin, el departamento sigue existiendo
- Múltiples admins pueden pertenecer al mismo departamento

**UML:** `UsuarioAdmin "*" --> "0..1" Departamento` (rombo vacío)

---

#### ASOCIACIÓN (Many-to-Many): UsuarioFinal ↔ Reclamo (vía AdherenteReclamo)

**Ubicación:** `modules/adherente_reclamo.py`

```python
class AdherenteReclamo(db.Model):
    """Tabla intermedia para relación N:M"""
    __tablename__ = "adherente_reclamo"
    reclamo_id: Mapped[int] = mapped_column(ForeignKey("reclamo.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"))

    __table_args__ = (UniqueConstraint("reclamo_id", "usuario_id"),)
```

**Justificación:**
- Un usuario puede apoyar **MUCHOS** reclamos
- Un reclamo puede tener **MUCHOS** adherentes
- Ambos existen **INDEPENDIENTEMENTE**
- `UniqueConstraint` evita adhesiones duplicadas

---

#### DEPENDENCIA: Reclamo ··> Clasificador

**Ubicación:** `modules/reclamo.py`

```python
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

**Justificación:**
- Reclamo **USA** clasificador para una tarea específica
- No almacena una instancia de clasificador como atributo
- La relación es temporal (solo durante la ejecución del método)

**UML:** `Reclamo ..> Clasificador` (línea punteada)

---

## PREGUNTA 3: Polimorfismo de subtipos

### ¿En qué consiste el polimorfismo de subtipos?

El **polimorfismo de subtipos** permite que un objeto de una clase derivada pueda ser tratado como un objeto de su clase base, pero manteniendo su comportamiento específico.

**Características:**
1. Un subtipo puede sustituir a su supertipo
2. El mismo mensaje a diferentes objetos produce respuestas diferentes
3. Se decide en tiempo de ejecución qué método llamar (dynamic dispatch)
4. Permite escribir código genérico que funciona con múltiples tipos

---

### Ejemplo con código del TP

**Ubicación:** `modules/usuario.py`, `modules/usuario_final.py`, `modules/usuario_admin.py`

```python
# ==================== CLASE BASE ABSTRACTA ====================
# modules/usuario.py
class MetaModeloABC(ABCMeta, type(db.Model)):
    """Metaclase combinada para resolver conflicto ABC + SQLAlchemy"""
    pass

class Usuario(UserMixin, db.Model, ABC, metaclass=MetaModeloABC):
    """Clase base — define la interfaz con método abstracto"""
    id: Mapped[int]
    nombre: Mapped[str]
    apellido: Mapped[str]

    @property
    @abstractmethod
    def nombre_completo(self) -> str:
        """Método polimórfico — cada subtipo lo redefine"""
        pass

# ==================== SUBTIPOS ====================
# modules/usuario_final.py
class UsuarioFinal(Usuario):
    """Subtipo 1 — implementación específica"""
    claustro: Mapped[Claustro | None]

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.claustro.value}"

# modules/usuario_admin.py
class UsuarioAdmin(Usuario):
    """Subtipo 2 — implementación diferente"""
    rol_admin: Mapped[RolAdmin | None]

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido} - {self.rol_admin.value}"

# ==================== USO POLIMÓRFICO ====================
# modules/rutas.py
@login_manager.user_loader
def cargar_usuario(usuario_id):
    return Usuario.obtener_por_id(int(usuario_id))
    # Retorna UsuarioFinal o UsuarioAdmin según tipo_usuario

# En cualquier template o ruta:
# current_user.nombre_completo → llama al método correcto según el tipo real

# ==================== OTRO EJEMPLO ====================
def enviar_notificacion_a_usuarios(usuarios: list[Usuario]):
    """Función genérica que acepta cualquier subtipo de Usuario."""
    for usuario in usuarios:
        mensaje = f"Hola {usuario.nombre_completo}, tienes una notificación"
        print(mensaje)
        # Si es UsuarioFinal: "Hola Juan Pérez - estudiante, ..."
        # Si es UsuarioAdmin: "Hola Ana López - jefe_departamento, ..."
```

**Ventajas del polimorfismo en este ejemplo:**
1. **Código genérico:** `cargar_usuario()` funciona con cualquier tipo de usuario
2. **Extensibilidad:** Si agrego `UsuarioModerador`, no cambio el código existente
3. **Mantenibilidad:** Cada clase maneja su propia implementación
4. **Principio Open/Closed:** Abierto a extensión, cerrado a modificación

---

## PREGUNTA 4: Principios SOLID

### PRINCIPIO 1: Single Responsibility Principle (SRP)

#### Enunciado

> **Una clase debe tener una única razón para cambiar.**

#### Relación con el diseño del TP

**Ejemplo 1: Separación de Responsabilidades**

```python
# ==================== Responsabilidad 1: Gestionar Reclamos ====================
# modules/reclamo.py
class Reclamo(db.Model):
    """ÚNICA RESPONSABILIDAD: Gestionar reclamos"""
    @staticmethod
    def crear(creador_id, detalle, departamento_id=None, ruta_imagen=None): ...
    @staticmethod
    def actualizar_estado(reclamo_id, nuevo_estado, cambiado_por_id): ...
    @staticmethod
    def obtener_por_id(reclamo_id): ...

# ==================== Responsabilidad 2: Notificaciones ====================
# modules/notificacion_usuario.py
class NotificacionUsuario(db.Model):
    """ÚNICA RESPONSABILIDAD: Gestionar notificaciones"""
    @staticmethod
    def obtener_pendientes_usuario(usuario_id): ...
    @staticmethod
    def obtener_conteo_no_leidas(usuario_id): ...

# ==================== Responsabilidad 3: Clasificación ====================
# modules/clasificador.py
class Clasificador:
    """ÚNICA RESPONSABILIDAD: Clasificar texto con ML (modelo provisto por cátedra)"""
    def clasificar(self, texto) -> str: ...
    def modelo_disponible(self) -> bool: ...

# ==================== Responsabilidad 4: Imágenes ====================
# modules/manejador_imagen.py
class ManejadorImagen:
    """ÚNICA RESPONSABILIDAD: Gestionar imágenes"""
    @staticmethod
    def validar_imagen(archivo): ...
    @staticmethod
    def guardar_imagen_reclamo(archivo): ...
```

**Ventaja:** Si necesito cambiar cómo se clasifican los reclamos, solo modifico `Clasificador`, no todo el sistema.

---

### PRINCIPIO 2: Dependency Inversion Principle (DIP)

#### Enunciado

> **Los módulos de alto nivel no deben depender de módulos de bajo nivel. Ambos deben depender de abstracciones.**

#### Relación con el diseño del TP

**Ejemplo 1: Abstracción de Base de Datos**

```python
# modules/reclamo.py
class Reclamo(db.Model):
    @staticmethod
    def crear(creador_id, detalle, departamento_id=None, ruta_imagen=None):
        reclamo = Reclamo(detalle=detalle, ...)
        # Depende de la ABSTRACCIÓN 'db', no de una implementación concreta
        db.session.add(reclamo)  # ← No sabe si es SQLite, PostgreSQL, MySQL
        db.session.commit()
        return reclamo, None

# modules/config.py — Abstracción
db = SQLAlchemy(model_class=Base)  # Abstracción que puede usar cualquier motor SQL
# SQLALCHEMY_DATABASE_URI = "sqlite:///reclamos.db"  # desarrollo
# SQLALCHEMY_DATABASE_URI = "postgresql://..."        # producción
```

**Ejemplo 2: Abstracción del Clasificador**

```python
# modules/reclamo.py
class Reclamo(db.Model):
    @staticmethod
    def _clasificar_departamento(detalle: str) -> int | None:
        # Depende de la INTERFAZ de clasificador, no de la implementación
        nombre_predicho = clasificador.clasificar(detalle)
        # ↑ Solo conoce el método .clasificar(), no si usa TF-IDF, BERT, etc.

# modules/clasificador.py — Implementación actual (pickle provisto por cátedra)
class Clasificador:
    def clasificar(self, texto: str) -> str:
        # Carga modelo desde data/claims_clf.pkl
        resultado = self.__clf.classify([texto])[0]
        return tabla_mapeo[resultado]
    # Si cambio el modelo, Reclamo NO cambia
```

**Ejemplo 3: Decoradores como Abstracción**

```python
# modules/utils/decoradores.py
def admin_requerido(f):
    """Abstracción de control de acceso"""
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not isinstance(current_user, UsuarioAdmin):
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return funcion_decorada

# modules/rutas.py
@app.route("/admin/", endpoint="admin.dashboard")
@admin_requerido  # ← No sabe CÓMO se verifica, solo que SE verifica
def dashboard_admin():
    return render_template("admin/dashboard.html")
```

---

## PREGUNTA 5: Estructura AAA de las pruebas unitarias

### ¿En qué consiste la estructura AAA?

La estructura **AAA** (Arrange-Act-Assert) es un patrón para organizar pruebas unitarias en tres secciones:

1. **Arrange (Preparar):** Configurar el escenario de prueba
2. **Act (Actuar):** Ejecutar la acción que se está probando
3. **Assert (Verificar):** Comprobar que el resultado es el esperado

---

### Ejemplo con código del TP

**Ubicación:** `tests/test_reclamo.py`

```python
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
            correo="testuser@test.com", nombre_usuario="testuser",
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
        self.assertIsNotNone(reclamo, "Debería crear el reclamo")
        self.assertIsNone(error, "No debería haber error")
        self.assertEqual(reclamo.detalle, detalle)
        self.assertEqual(reclamo.departamento_id, depto_id)
        self.assertEqual(reclamo.estado, EstadoReclamo.PENDIENTE)
        self.assertEqual(reclamo.creador_id, usuario_id)
```

**Ejemplo con validación de error:**

```python
    def test_crear_reclamo_con_detalle_vacio(self):
        # ==================== ARRANGE ====================
        detalle_vacio = "   "
        depto_id = self.depto1_id

        # ==================== ACT ====================
        reclamo, error = Reclamo.crear(
            creador_id=self.usuario.id, detalle=detalle_vacio,
            departamento_id=depto_id,
        )

        # ==================== ASSERT ====================
        self.assertIsNone(reclamo, "No debería crear el reclamo")
        self.assertIsNotNone(error, "Debería retornar un mensaje de error")
```

**Ejemplo con configuración compleja:**

```python
    def test_adherente_duplicado(self):
        # ==================== ARRANGE ====================
        reclamo, _ = Reclamo.crear(
            creador_id=self.usuario.id,
            detalle="Problema de prueba",
            departamento_id=self.depto1_id,
        )

        adherente = UsuarioFinal(
            nombre="María", apellido="García",
            correo="maria@example.com", nombre_usuario="maria",
            claustro=Claustro.ESTUDIANTE,
        )
        adherente.establecer_contrasena("password")
        db.session.add(adherente)
        db.session.commit()

        # Primera adhesión (debe funcionar)
        primer_resultado, _ = Reclamo.agregar_adherente(reclamo.id, adherente.id)
        self.assertTrue(primer_resultado)

        # ==================== ACT ====================
        segundo_resultado, segundo_error = Reclamo.agregar_adherente(
            reclamo.id, adherente.id,
        )

        # ==================== ASSERT ====================
        self.assertFalse(segundo_resultado, "No debería adherirse dos veces")
        self.assertIsNotNone(segundo_error)
        self.assertEqual(reclamo.cantidad_adherentes, 1)
```

---

## PREGUNTA 6: Protocolo de iteradores en Python

### ¿En qué consiste el protocolo de iteradores?

El **protocolo de iteradores** permite **recorrer elementos de una colección de forma secuencial** sin exponer su estructura interna. Se basa en dos métodos:

1. **`__iter__()`:** Retorna el objeto iterador (generalmente `self`)
2. **`__next__()`:** Retorna el siguiente elemento o lanza `StopIteration`

**¿Cómo funciona un for loop internamente?**

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

---

### Ejemplo con código del TP

**Ejemplo 1: Iterador personalizado**

```python
# Ejemplo educativo aplicable al contexto del TP
class IteradorReclamos:
    """Iterador personalizado para recorrer reclamos"""
    def __init__(self, reclamos: list):
        self.reclamos = reclamos
        self.indice = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.indice < len(self.reclamos):
            reclamo = self.reclamos[self.indice]
            self.indice += 1
            return reclamo
        else:
            raise StopIteration

# Uso:
reclamos = [reclamo1, reclamo2, reclamo3]
iterador = IteradorReclamos(reclamos)
for reclamo in iterador:
    print(f"Reclamo #{reclamo.id}: {reclamo.detalle}")
```

**Ejemplo 2: Iterador lazy con batches**

```python
# Ejemplo hipotético aplicable al TP
class IteradorReclamosPorEstado:
    """Carga reclamos en batches — eficiente en memoria"""
    def __init__(self, estado: EstadoReclamo, batch_size: int = 50):
        self.estado = estado
        self.batch_size = batch_size
        self.offset = 0
        self.batch_actual = []
        self.indice_batch = 0

    def __iter__(self):
        return self

    def __next__(self) -> Reclamo:
        if self.indice_batch >= len(self.batch_actual):
            self.batch_actual = (
                Reclamo.query
                .filter_by(estado=self.estado)
                .offset(self.offset).limit(self.batch_size).all()
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
    print(f"Procesando reclamo #{reclamo.id}")
```

**Ejemplo 3: Generador con yield**

```python
# Ejemplo hipotético aplicable al TP
class Reclamo(db.Model):
    @staticmethod
    def iterar_por_departamento(departamento_id: int):
        """Generador — yield convierte la función en un iterador"""
        offset = 0
        batch_size = 100
        while True:
            reclamos = (
                Reclamo.query
                .filter_by(departamento_id=departamento_id)
                .offset(offset).limit(batch_size).all()
            )
            if not reclamos:
                break
            for reclamo in reclamos:
                yield reclamo  # ← Pausa aquí y retorna reclamo
            offset += batch_size

for reclamo in Reclamo.iterar_por_departamento(departamento_id=1):
    print(reclamo.detalle)
```

**Ejemplo 4: Objetos iterables existentes en el TP**

```python
# modules/reclamo.py — Las relaciones son ITERABLES
reclamo = Reclamo.obtener_por_id(1)

# Iterar sobre adherentes (usa __iter__ internamente)
for adherente in reclamo.adherentes:
    print(f"Adherente: {adherente.usuario.nombre_completo}")

# Iterar sobre historial
for historial in reclamo.historial_estados:
    print(f"{historial.cambiado_en}: {historial.estado_anterior} → {historial.estado_nuevo}")

# Comprehensions también usan el protocolo de iteradores:
pendientes = [r for r in Reclamo.query.all() if r.estado == EstadoReclamo.PENDIENTE]
total_adherentes = sum(r.cantidad_adherentes for r in reclamos)
```

---

## TABLA RESUMEN - Ubicaciones Rápidas

| Concepto | Archivo Principal | Ejemplo Clave |
|----------|-------------------|---------------|
| **Herencia** | `modules/usuario.py`, `usuario_final.py`, `usuario_admin.py` | Usuario → UsuarioFinal, UsuarioAdmin |
| **ABC / Metaclase** | `modules/usuario.py`, `modules/generador_reportes.py` | MetaModeloABC, Reporte abstracto |
| **Composición** | `modules/reclamo.py` | `cascade="all, delete-orphan"` |
| **Agregación** | `modules/usuario_admin.py` | UsuarioAdmin → Departamento |
| **Asociación N:M** | `modules/adherente_reclamo.py` | UsuarioFinal ↔ Reclamo |
| **Polimorfismo** | `modules/usuario*.py` | `nombre_completo` diferente por subtipo |
| **SRP** | `modules/reclamo.py`, `notificacion_usuario.py` | Módulos separados |
| **DIP** | `modules/reclamo.py` | Depende de `db` abstracto |
| **AAA** | `tests/test_reclamo.py` | Arrange-Act-Assert |
| **Iteradores** | Relaciones en `modules/reclamo.py` | `for adherente in reclamo.adherentes` |
| **unittest** | `tests/conftest.py`, `test_*.py` | `CasoTestBase`, `setUp()`, `tearDown()` |
| **Factory** | `modules/generador_reportes.py` | `crear_reporte()` → ReporteHTML/PDF |

---

**Fin del documento de defensa**
