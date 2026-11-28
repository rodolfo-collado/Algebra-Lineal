"""Almacén local de resoluciones y ejercicios en SQLite (biblioteca estándar).

Cada operación abre su propia conexión: Waitress atiende en varios hilos y dos ventanas
de la app pueden compartir el archivo; SQLite coordina los bloqueos entre procesos.

Errores, de menor a mayor gravedad:

- Bloqueo, permisos o disco (``AlmacenNoDisponible``): temporal. No se toca el archivo;
  la página lo explica y la próxima operación lo vuelve a intentar.
- Fila con un documento ilegible: se lista como «no se puede abrir» y puede eliminarse;
  el resto del cuaderno sigue intacto.
- Archivo dañado (SQLite informa SQLITE_CORRUPT o SQLITE_NOTADB, o ``quick_check`` falla):
  se aparta con otro nombre, nunca se borra, y se empieza un archivo nuevo.
"""

import sqlite3
import threading
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from . import contrato


VERSION_BASE = 1
MAX_DOCUMENTO = 4 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_NOMBRE = 120
# Códigos primarios de SQLite que significan un archivo dañado, no un problema de acceso.
_CORRUPCION = {11, 26}  # SQLITE_CORRUPT, SQLITE_NOTADB

_TABLAS = """
CREATE TABLE IF NOT EXISTS ejercicios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    creado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resoluciones (
    id INTEGER PRIMARY KEY,
    huella TEXT NOT NULL UNIQUE,
    ruta TEXT NOT NULL,
    herramienta TEXT NOT NULL,
    nombre TEXT NOT NULL,
    ejercicio INTEGER REFERENCES ejercicios(id) ON DELETE SET NULL,
    creado TEXT NOT NULL,
    usado TEXT NOT NULL,
    documento TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS resoluciones_ejercicio ON resoluciones(ejercicio);
"""

# Estado legible sin decodificar documentos enteros: JSON válido, contrato y versión.
_ESTADO = f"""
    CASE
        WHEN NOT json_valid(documento) THEN 'danado'
        WHEN json_extract(documento, '$.contrato') IS NOT '{contrato.CONTRATO}' THEN 'danado'
        WHEN json_type(documento, '$.version') IS NOT 'integer' THEN 'danado'
        WHEN json_extract(documento, '$.version') > {contrato.VERSION} THEN 'futuro'
        ELSE 'ok'
    END
"""
_COLUMNAS = f"""
    id, ruta, herramienta, nombre, ejercicio, creado, usado, {_ESTADO} AS estado,
    CASE WHEN json_valid(documento) THEN json_extract(documento, '$.herramienta.esquema') END AS esquema,
    CASE WHEN json_valid(documento) THEN json_extract(documento, '$.resumen') END AS resumen
"""


class AlmacenNoDisponible(Exception):
    """Bloqueo, permisos o disco: los datos siguen a salvo, el acceso falló esta vez."""


class AlmacenFuturo(AlmacenNoDisponible):
    """Una versión más reciente de PyGebra cambió el archivo: esta no lo modifica."""


class CuadernoLleno(Exception):
    """Guardar superaría el tamaño máximo del cuaderno o del documento."""


class _Corrupto(sqlite3.DatabaseError):
    pass


def _es_corrupcion(error):
    if isinstance(error, _Corrupto):
        return True
    codigo = getattr(error, "sqlite_errorcode", None)
    return codigo is not None and codigo & 0xFF in _CORRUPCION


def ahora():
    """Fecha local con zona: la del ajuste TIME_ZONE de Django, como el resto de la app."""
    return timezone.localtime().isoformat(timespec="seconds")


class Almacen:
    def __init__(self, archivo, espera=5):
        self.archivo = Path(archivo)
        # Segundos que SQLite espera a que otra ventana suelte el archivo antes de rendirse.
        self.espera = espera
        # Archivo dañado que este proceso apartó; el cuaderno lo informa.
        self.apartado = None
        self._verificado = False
        self._candado = threading.Lock()

    # ---- Conexión y recuperación ----

    def _abrir(self):
        self.archivo.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.archivo, timeout=self.espera)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            with self._candado:
                if not self._verificado:
                    # Una vez por proceso: detecta un archivo dañado antes de escribir en él.
                    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                        raise _Corrupto("quick_check")
                    self._migrar(db)
                    self._verificado = True
        except BaseException:
            db.close()
            raise
        return db

    def _migrar(self, db):
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > VERSION_BASE:
            raise AlmacenFuturo("El cuaderno lo creó una versión más reciente de PyGebra.")
        if version < VERSION_BASE:
            with db:
                db.executescript(_TABLAS)
                db.execute(f"PRAGMA user_version = {VERSION_BASE}")

    def _apartar(self):
        """Renombra el archivo dañado (y sus diarios) para empezar uno nuevo sin perderlo."""
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        destino = self.archivo.with_name(f"{self.archivo.stem}.apartado-{marca}{self.archivo.suffix}")
        try:
            self.archivo.replace(destino)
        except OSError:
            # Otro proceso lo tiene abierto (Windows) o no hay permiso: mejor no tocar nada.
            return False
        for sufijo in ("-wal", "-shm", "-journal"):
            diario = self.archivo.with_name(self.archivo.name + sufijo)
            try:
                diario.replace(destino.with_name(destino.name + sufijo))
            except FileNotFoundError:
                pass
            except OSError:
                pass  # El diario se queda; SQLite no lo usará con un archivo nuevo.
        self.apartado = destino
        self._verificado = False
        return True

    @contextmanager
    def conexion(self):
        """Transacción sobre el cuaderno; traduce los errores de SQLite a los de este módulo."""
        for intento in (1, 2):
            try:
                db = self._abrir()
                break
            except AlmacenNoDisponible:
                raise
            except sqlite3.DatabaseError as error:
                if intento == 1 and _es_corrupcion(error) and self._apartar():
                    continue
                raise AlmacenNoDisponible(str(error)) from error
            except OSError as error:
                raise AlmacenNoDisponible(str(error)) from error
        try:
            with closing(db), db:
                yield db
        except sqlite3.DatabaseError as error:
            if _es_corrupcion(error):
                # Se confirma con quick_check en la próxima apertura antes de apartar nada.
                self._verificado = False
            raise AlmacenNoDisponible(str(error)) from error
        except OSError as error:
            raise AlmacenNoDisponible(str(error)) from error

    # ---- Resoluciones ----

    def guardar(self, *, huella, ruta, herramienta, nombre, documento):
        """(id, nueva). Una huella repetida no duplica ni sobrescribe: solo se marca como usada."""
        tamano = len(documento.encode("utf-8"))
        if tamano > MAX_DOCUMENTO:
            raise CuadernoLleno("Esta resolución es demasiado grande para guardarla.")
        momento = ahora()
        with self.conexion() as db:
            # Reserva la escritura antes de comprobar: otra ventana no puede colar la misma huella.
            db.execute("BEGIN IMMEDIATE")
            existente = db.execute("SELECT id FROM resoluciones WHERE huella = ?", (huella,)).fetchone()
            if existente:
                db.execute("UPDATE resoluciones SET usado = ? WHERE id = ?", (momento, existente["id"]))
                return existente["id"], False
            total = db.execute("SELECT COALESCE(SUM(length(CAST(documento AS BLOB))), 0) FROM resoluciones").fetchone()[0]
            if total + tamano > MAX_TOTAL:
                raise CuadernoLleno("El cuaderno está lleno: elimina resoluciones que ya no necesites.")
            cursor = db.execute(
                "INSERT INTO resoluciones (huella, ruta, herramienta, nombre, creado, usado, documento)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (huella, ruta, herramienta, nombre[:MAX_NOMBRE], momento, momento, documento),
            )
            return cursor.lastrowid, True

    def listar(self):
        with self.conexion() as db:
            return [dict(f) for f in db.execute(f"SELECT {_COLUMNAS} FROM resoluciones ORDER BY usado DESC, id DESC")]

    def obtener(self, identificador, documento=True):
        """(metadatos, texto del documento), solo los metadatos con documento=False, o None."""
        columnas = f"{_COLUMNAS}, documento" if documento else _COLUMNAS
        with self.conexion() as db:
            fila = db.execute(f"SELECT {columnas} FROM resoluciones WHERE id = ?", (identificador,)).fetchone()
        if fila is None:
            return None
        datos = dict(fila)
        return (datos, datos.pop("documento")) if documento else datos

    def renombrar(self, identificador, nombre):
        with self.conexion() as db:
            return db.execute("UPDATE resoluciones SET nombre = ? WHERE id = ?",
                              (nombre[:MAX_NOMBRE], identificador)).rowcount

    def eliminar(self, identificadores):
        with self.conexion() as db:
            return db.executemany("DELETE FROM resoluciones WHERE id = ?", [(i,) for i in identificadores]).rowcount

    def agrupar(self, identificadores, ejercicio):
        """Mueve las resoluciones al ejercicio (None las deja sin agrupar)."""
        with self.conexion() as db:
            return db.executemany("UPDATE resoluciones SET ejercicio = ? WHERE id = ?",
                                  [(ejercicio, i) for i in identificadores]).rowcount

    # ---- Ejercicios ----

    def ejercicios(self):
        with self.conexion() as db:
            return [dict(f) for f in db.execute("SELECT id, nombre, creado FROM ejercicios ORDER BY id")]

    def crear_ejercicio(self, nombre):
        with self.conexion() as db:
            return db.execute("INSERT INTO ejercicios (nombre, creado) VALUES (?, ?)",
                              (nombre[:MAX_NOMBRE], ahora())).lastrowid

    def existe_ejercicio(self, identificador):
        with self.conexion() as db:
            return db.execute("SELECT 1 FROM ejercicios WHERE id = ?", (identificador,)).fetchone() is not None

    def renombrar_ejercicio(self, identificador, nombre):
        with self.conexion() as db:
            return db.execute("UPDATE ejercicios SET nombre = ? WHERE id = ?",
                              (nombre[:MAX_NOMBRE], identificador)).rowcount

    def disolver_ejercicio(self, identificador):
        """Quita el ejercicio; sus resoluciones vuelven a «Sueltas» (ON DELETE SET NULL)."""
        with self.conexion() as db:
            return db.execute("DELETE FROM ejercicios WHERE id = ?", (identificador,)).rowcount


_ALMACENES = {}
_ALMACENES_CANDADO = threading.Lock()


def almacen():
    """El almacén del archivo configurado (ALGEBRA_RESOLUCIONES o la carpeta de PyGebra)."""
    ruta = str(settings.RESOLUCIONES_ARCHIVO)
    with _ALMACENES_CANDADO:
        if ruta not in _ALMACENES:
            _ALMACENES[ruta] = Almacen(ruta)
        return _ALMACENES[ruta]
