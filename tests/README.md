# Tests

Esta carpeta contiene los tests del proyecto organizados por módulo/funcionalidad.

## Estructura

- `conftest.py` — Configuración base de tests con `CasoTestBase`
- `test_adherente_reclamo.py` — Tests para sistema de adherentes (`AdherenteReclamo`)
- `test_clasificador_unit.py` — Tests unitarios del clasificador (`Clasificador`)
- `test_historial_estado.py` — Tests para historial de estados de reclamos (`HistorialEstadoReclamo`)

## Ejecutar Tests

El proyecto usa **unittest** (biblioteca estándar de Python).

### Ejecutar todos los tests:
```bash
python -m unittest discover tests -v
```

### Ejecutar un archivo de test específico:
```bash
python -m unittest tests.test_adherente_reclamo
python -m unittest tests.test_clasificador_unit
python -m unittest tests.test_historial_estado
```

### Ejecutar una clase de test específica:
```bash
python -m unittest tests.test_adherente_reclamo.TestAdherenteReclamo
```

### Ejecutar un test individual:
```bash
python -m unittest tests.test_adherente_reclamo.TestAdherenteReclamo.test_agregar_adherente_exitoso
```

### Opciones útiles:
```bash
# Con salida detallada (verbose)
python -m unittest discover tests -v

# Detener en el primer fallo
python -m unittest discover tests -f
```

## Clase Base: `CasoTestBase`

Ubicación: `tests/conftest.py`

Todos los tests heredan de `CasoTestBase`, que hereda de `unittest.TestCase` y provee:

- Creación de una aplicación Flask de prueba con base de datos SQLite en memoria
- Creación automática de departamentos de prueba (`secretaria_tecnica`, `ciencias`, `humanidades`)
- Limpieza de la base de datos después de cada test con `tearDown()`
- IDs de departamentos disponibles en `self.departamentos_prueba`

```python
from tests.conftest import CasoTestBase
from modules.config import db

class TestMiFuncionalidad(CasoTestBase):

    def setUp(self):
        super().setUp()
        # Configuración adicional si es necesaria

    def test_caso_exitoso(self):
        # Arrange — preparar datos
        # Act — ejecutar la funcionalidad
        # Assert — verificar resultados
        self.assertEqual(resultado_esperado, resultado_actual)
```

## Guía para Agregar Nuevos Tests

Cuando implementes una nueva funcionalidad, **siempre crea tests básicos** que verifiquen:

1. **Casos exitosos**: La funcionalidad funciona correctamente con datos válidos
2. **Casos de error**: Manejo correcto de errores con datos inválidos
3. **Validaciones**: Todas las restricciones y validaciones funcionan
4. **Edge cases**: Casos límite y situaciones especiales

### Plantilla para nuevos tests:

```python
"""
Tests para [Nombre del Módulo]
"""
import unittest

from modules.config import db
from modules.reclamo import Reclamo, EstadoReclamo
from modules.usuario_final import UsuarioFinal, Claustro
from tests.conftest import CasoTestBase


class TestMiFuncionalidad(CasoTestBase):
    """Tests para la funcionalidad X"""

    def setUp(self):
        """Configuración antes de cada test"""
        super().setUp()
        # Crear usuario de prueba
        self.usuario = UsuarioFinal(
            nombre="Test", apellido="Usuario",
            correo="test@test.com", nombre_usuario="testuser",
            claustro=Claustro.ESTUDIANTE,
        )
        self.usuario.establecer_contrasena("test123")
        db.session.add(self.usuario)
        db.session.commit()

    def test_caso_exitoso(self):
        """Descripción de qué prueba este test"""
        # Arrange — preparar datos
        detalle = "Problema de prueba"
        depto_id = self.departamentos_prueba["depto1_id"]

        # Act — ejecutar la funcionalidad
        reclamo, error = Reclamo.crear(
            usuario_id=self.usuario.id,
            detalle=detalle,
            departamento_id=depto_id,
        )

        # Assert — verificar resultados
        self.assertIsNotNone(reclamo)
        self.assertIsNone(error)
        self.assertEqual(reclamo.detalle, detalle)

    def test_caso_de_error(self):
        """Test que verifica manejo de errores"""
        reclamo, error = Reclamo.crear(
            usuario_id=self.usuario.id,
            detalle="   ",
            departamento_id=self.departamentos_prueba["depto1_id"],
        )
        self.assertIsNone(reclamo)
        self.assertIsNotNone(error)


if __name__ == '__main__':
    unittest.main()
```

### Assertions comunes en unittest:

- `assertEqual(a, b)` — Verifica que a == b
- `assertNotEqual(a, b)` — Verifica que a != b
- `assertTrue(x)` / `assertFalse(x)` — Verifica booleano
- `assertIsNone(x)` / `assertIsNotNone(x)` — Verifica None
- `assertIn(a, b)` / `assertNotIn(a, b)` — Verifica membresía
- `assertRaises(Exception)` — Verifica que se lanza excepción
- `assertGreater(a, b)` / `assertLess(a, b)` — Comparaciones numéricas
- `assertIsInstance(a, type)` — Verifica tipo

## Convenciones

- Usa nombres descriptivos: `test_nombre_funcionalidad.py`
- Agrupa tests relacionados en el mismo archivo
- Usa patrón AAA (Arrange-Act-Assert) en cada test
- Documenta qué prueba cada test con docstrings
- Limpia datos de prueba si es necesario (automático con `CasoTestBase`)
