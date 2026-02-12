"""
Punto de entrada para la aplicación Flask.
Este módulo importa la app y las rutas, y ejecuta el servidor de desarrollo.
"""

# Import app from config
from modules.config import app

# Import routes to register them with the app
import modules.rutas  # noqa: F401


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
