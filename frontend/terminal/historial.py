"""Historial y preferencias locales de la consola."""

from contextlib import closing
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

from platformdirs import user_data_path

from .adaptador import Tabla
from .conjuntos import RepresentacionConjuntos
from .graficas import Curva, PasoGrafico


@dataclass(frozen=True)
class Ejercicio:
    comando: str
    titulo: str
    datos: dict
    bloques: tuple
    archivos: tuple[str, ...] = ()
    grafica: Curva | RepresentacionConjuntos | None = None

    def serializar(self):
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def leer(cls, texto):
        datos = json.loads(texto)
        bloques = tuple(
            Tabla(b["titulo"], tuple(b["columnas"]), tuple(map(tuple, b["filas"]))) if isinstance(b, dict) else b
            for b in datos["bloques"]
        )
        grafica = datos["grafica"]
        if grafica and "x" in grafica:
            vista = Curva(grafica["etiqueta"], tuple(grafica["x"]), tuple(grafica["y"]), tuple(
                PasoGrafico(p["descripcion"], tuple(map(tuple, p["puntos"])), p["segmento"])
                for p in grafica["pasos"]
            ))
        else:
            vista = RepresentacionConjuntos(**grafica) if grafica else None
        return cls(datos["comando"], datos["titulo"], datos["datos"], bloques, tuple(datos["archivos"]), vista)


class Historial:
    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo is not None else user_data_path(
            "PyGebra", appauthor=False,
        ) / "consola.sqlite3"

    def abrir(self):
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS ejercicios (id INTEGER PRIMARY KEY, datos TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS ajustes (clave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
            historial = [Ejercicio.leer(datos) for (datos,) in db.execute("SELECT datos FROM ejercicios ORDER BY id")]
            ajustes = dict(db.execute("SELECT clave, valor FROM ajustes"))
        return historial, ajustes

    def agregar(self, ejercicio):
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("INSERT INTO ejercicios (datos) VALUES (?)", (ejercicio.serializar(),))

    def preferencia(self, clave, valor):
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("INSERT OR REPLACE INTO ajustes (clave, valor) VALUES (?, ?)", (clave, valor))
