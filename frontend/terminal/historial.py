"""Historial y preferencias locales de la consola."""

from contextlib import closing
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sqlite3

from platformdirs import user_data_path

from .adaptador import Linea, Tabla
from .conjuntos import RepresentacionConjuntos
from .graficas import Curva, MarcaGrafica, PasoGrafico


@dataclass(frozen=True)
class Ejercicio:
    comando: str
    titulo: str
    datos: dict
    bloques: tuple
    archivos: tuple[str, ...] = ()
    grafica: Curva | RepresentacionConjuntos | None = None

    def serializar(self):
        datos = asdict(self)
        datos["bloques"] = [
            {"texto": str(b), "estilo": b.estilo} if isinstance(b, Linea) else b for b in datos["bloques"]
        ]
        return json.dumps(datos, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def leer(cls, texto):
        datos = json.loads(texto)
        bloques = tuple(cls._leer_bloque(b) for b in datos["bloques"])
        grafica = datos["grafica"]
        if grafica and "x" in grafica:
            pasos = tuple(PasoGrafico(p["descripcion"], tuple(map(tuple, p["puntos"])), p["segmento"])
                          for p in grafica["pasos"])
            marcas = tuple(MarcaGrafica(**marca) for marca in grafica.get("marcas", ()))
            vista = Curva(grafica["etiqueta"], tuple(grafica["x"]), tuple(grafica["y"]), pasos, marcas)
        else:
            vista = RepresentacionConjuntos(**grafica) if grafica else None
        return cls(datos["comando"], datos["titulo"], datos["datos"], bloques, tuple(datos["archivos"]), vista)

    @staticmethod
    def _leer_bloque(bloque):
        if isinstance(bloque, str):
            return Linea.legada(bloque)
        if "texto" in bloque:
            return Linea(bloque["texto"], bloque["estilo"])
        return Tabla(bloque["titulo"], tuple(bloque["columnas"]), tuple(map(tuple, bloque["filas"])))


class Historial:
    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo is not None else user_data_path(
            "PyGebra", appauthor=False,
        ) / "consola.sqlite3"
        # Registros que no se pudieron leer en la última apertura; siguen en el archivo.
        self.omitidos = 0

    def abrir(self):
        """Ejercicios legibles y ajustes. Un registro dañado se omite sin perder los demás."""
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS ejercicios (id INTEGER PRIMARY KEY, datos TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS ajustes (clave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
            filas = db.execute("SELECT datos FROM ejercicios ORDER BY id").fetchall()
            ajustes = dict(db.execute("SELECT clave, valor FROM ajustes"))
        historial = []
        for (datos,) in filas:
            try:
                historial.append(Ejercicio.leer(datos))
            except (TypeError, ValueError, KeyError, AttributeError, IndexError):
                continue
        self.omitidos = len(filas) - len(historial)
        return historial, ajustes

    def agregar(self, ejercicio):
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("INSERT INTO ejercicios (datos) VALUES (?)", (ejercicio.serializar(),))

    def preferencia(self, clave, valor):
        with closing(sqlite3.connect(self.archivo)) as db, db:
            db.execute("INSERT OR REPLACE INTO ajustes (clave, valor) VALUES (?, ?)", (clave, valor))
