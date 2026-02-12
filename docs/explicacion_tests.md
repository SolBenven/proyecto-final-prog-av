# Explicación de los Tests del Proyecto

El proyecto utiliza **unittest** (biblioteca estándar de Python) como framework de testing. Los tests se encuentran en la carpeta `tests/`.

---

## 1. Configuración Base — `conftest.py`

**Archivo:** `tests/conftest.py`  
**Clase:** `CasoTestBase` (hereda de `unittest.TestCase`)

Este archivo define la clase base de la cual heredan la mayoría de los tests. Provee la infraestructura necesaria para que cada test se ejecute de forma aislada con su propia base de datos.

### ¿Qué hace?

- **`setUp()`** — Antes de CADA test:
  - Crea una aplicación Flask en modo `TESTING`.
  - Configura una base de datos SQLite **en memoria** (no toca la DB real).
  - Desactiva la protección CSRF para facilitar las pruebas.
  - Crea todas las tablas de la base de datos.
  - Crea **3 departamentos de prueba**:
    1. `"secretaria_tecnica"` — Secretaría Técnica (`es_secretaria_tecnica=True`)
    2. `"ciencias"` — Departamento de Ciencias
    3. `"humanidades"` — Departamento de Humanidades
  - Guarda los IDs en `self.departamentos_prueba` (claves: `"st_id"`, `"depto1_id"`, `"depto2_id"`).

- **`tearDown()`** — Después de CADA test:
  - Remueve la sesión de la base de datos.
  - Elimina todas las tablas.
  - Cierra el contexto de la aplicación.

> Esto garantiza que cada test empiece con una base de datos limpia y no haya interferencia entre tests.

---

## 2. Tests de Adherentes — `test_adherente_reclamo.py`

**Archivo:** `tests/test_adherente_reclamo.py`  
**Clase:** `TestAdherenteReclamo`  
**Módulo testeado:** `Reclamo` (funcionalidad de adherentes)

**Propósito:** Verificar que el sistema de adhesión a reclamos funcione correctamente. Un usuario puede "adherirse" a un reclamo existente para mostrar que también le afecta.

### Setup del test
- Crea un usuario "Creador" (docente) que crea el reclamo.
- Crea un usuario "Adherente" (estudiante) que se va a adherir.
- Crea un reclamo base en el departamento de Ciencias.

### Tests (11 tests)

| Test | Descripción |
|------|-------------|
| `test_agregar_adherente_exitoso` | Verifica que un usuario puede adherirse exitosamente a un reclamo. Espera: éxito=True, error=None. |
| `test_es_usuario_adherente_verdadero` | Verifica que después de adherirse, `es_usuario_adherente` retorna True. |
| `test_es_usuario_adherente_falso` | Verifica que si un usuario NO está adherido, `es_usuario_adherente` retorna False. |
| `test_agregar_adherente_dos_veces_falla` | Verifica que un usuario no puede adherirse dos veces al mismo reclamo. Espera: éxito=False. |
| `test_creador_no_puede_adherirse_propio_reclamo` | Verifica que el creador del reclamo no puede adherirse a su propio reclamo. |
| `test_quitar_adherente_exitoso` | Verifica que un usuario puede quitar su adhesión a un reclamo. |
| `test_quitar_adherente_cuando_no_adherido` | Verifica que no se puede quitar la adhesión si no está adherido. |
| `test_agregar_adherente_reclamo_invalido` | Verifica que no se puede adherir a un reclamo que no existe (ID=9999). |
| `test_obtener_adheridos_por_usuario` | Verifica que retorna la lista de reclamos a los que el usuario está adherido. |
| `test_obtener_ids_adherentes` | Verifica que retorna los IDs de todos los usuarios adheridos a un reclamo. |
| `test_multiples_adherentes` | Verifica que múltiples usuarios pueden adherirse al mismo reclamo simultáneamente. |

---

## 3. Tests del Clasificador — `test_clasificador_unit.py`

**Archivo:** `tests/test_clasificador_unit.py`  
**Clase:** `TestClasificador` (hereda de `unittest.TestCase` — **NO usa CasoTestBase**)  
**Módulo testeado:** `Clasificador`

**Propósito:** Verificar que el clasificador automático de reclamos funcione correctamente. El clasificador utiliza un **modelo pre-entrenado provisto por la cátedra** (`data/claims_clf.pkl`).

> **Nota:** Este test NO usa la base de datos, trabaja con el clasificador de forma aislada.

> **Importante:** El modelo viene pre-entrenado y no se entrena localmente. Los tests verifican la carga del modelo y el método `clasificar()`.

### Tests

| Test | Descripción |
|------|-------------|
| `test_modelo_disponible` | Verifica que `modelo_disponible()` retorna True si el pickle existe. |
| `test_clasificar_retorna_departamento` | Verifica que `clasificar(texto)` retorna un nombre de departamento válido. |
| `test_predicciones_consistentes` | Verifica que clasificar el mismo texto dos veces produce el mismo resultado. |

---

## 4. Tests de Historial de Estados — `test_historial_estado.py`

**Archivo:** `tests/test_historial_estado.py`  
**Clase:** `TestHistorialEstadoReclamo`  
**Módulo testeado:** `HistorialEstadoReclamo`

**Propósito:** Verificar que el sistema de historial de cambios de estado de reclamos funcione correctamente, registrando todos los cambios con timestamps y usuarios responsables.

### Setup del test
- Crea un usuario final que crea un reclamo.
- Crea un usuario admin que puede cambiar estados.
- Crea un reclamo en estado PENDIENTE.

### Tests

Verifica la creación de registros en el historial cuando cambia el estado de un reclamo, el seguimiento correcto de estados anteriores y nuevos, y la capacidad de consultar el historial completo de un reclamo.

---

## Resumen General

El proyecto cuenta con **3 archivos de tests** que cubren las funcionalidades clave:

| Área funcional | Archivo de test |
|----------------|:----------------|
| Sistema de adherentes | `test_adherente_reclamo.py` |
| Clasificador automático | `test_clasificador_unit.py` |
| Historial de estados | `test_historial_estado.py` |

**Archivos de test:** 3  
**Clase base:** `CasoTestBase` (en `conftest.py`)

---

## Cómo ejecutar los tests

```bash
# Todos los tests
python -m unittest discover tests -v

# Un archivo específico
python -m unittest tests.test_adherente_reclamo -v

# Un test individual
python -m unittest tests.test_adherente_reclamo.TestAdherenteReclamo.test_agregar_adherente_exitoso -v
```
