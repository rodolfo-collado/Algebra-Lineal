import sys
from pathlib import Path

# Los modulos de Semana_1 se importan entre si de forma plana, asi que las
# pruebas necesitan esa carpeta en sys.path en lugar de tratarla como paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Semana_1"))
