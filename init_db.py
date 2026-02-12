import os

from modules.config import create_app, db

# Importar todos los modelos para que SQLAlchemy los reconozca
import modules  # noqa: F401

app = create_app()

with app.app_context():
    # Ensure the instance directory exists
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)

    db.create_all()
    print("Base de datos inicializada y tablas creadas correctamente.")
