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

Organización (versión 2 de la base): Proyecto → Sección (opcional) → Ejercicio → Resoluciones.
Los ejercicios y las resoluciones pueden quedar fuera de todo proyecto. Cada elemento tiene su
``posicion`` dentro de su contenedor e ``incluir`` para el borrador del documento: excluir algo de
la exportación nunca lo borra. Quitar un proyecto, una sección o un ejercicio deja sus contenidos.
"""

import re
import sqlite3
import threading
from contextlib import closing, contextmanager
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from . import contrato


VERSION_BASE = 2
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

# v1 → v2: proyectos, secciones, numeración, orden y selección para exportar. Solo añade.
_MIGRACION_2 = """
CREATE TABLE proyectos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    objetivo INTEGER,
    creado TEXT NOT NULL
);
CREATE TABLE secciones (
    id INTEGER PRIMARY KEY,
    proyecto INTEGER NOT NULL REFERENCES proyectos(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    posicion INTEGER NOT NULL DEFAULT 0,
    incluir INTEGER NOT NULL DEFAULT 1
);
ALTER TABLE ejercicios ADD COLUMN proyecto INTEGER REFERENCES proyectos(id) ON DELETE SET NULL;
ALTER TABLE ejercicios ADD COLUMN seccion INTEGER REFERENCES secciones(id) ON DELETE SET NULL;
ALTER TABLE ejercicios ADD COLUMN numero TEXT;
ALTER TABLE ejercicios ADD COLUMN enunciado TEXT;
ALTER TABLE ejercicios ADD COLUMN posicion INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ejercicios ADD COLUMN incluir INTEGER NOT NULL DEFAULT 1;
ALTER TABLE resoluciones ADD COLUMN posicion INTEGER NOT NULL DEFAULT 0;
ALTER TABLE resoluciones ADD COLUMN incluir INTEGER NOT NULL DEFAULT 1;
UPDATE ejercicios SET posicion = id;
UPDATE resoluciones SET posicion = id;
CREATE TABLE ajustes (clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE INDEX ejercicios_proyecto ON ejercicios(proyecto, seccion, posicion);
CREATE INDEX secciones_proyecto ON secciones(proyecto, posicion);
"""
MIGRACIONES = {1: _TABLAS, 2: _MIGRACION_2}
# Contenedor de cada elemento ordenable: se reordena solo entre sus hermanos.
_HERMANOS = {"ejercicios": ("proyecto", "seccion"), "resoluciones": ("ejercicio",), "secciones": ("proyecto",)}

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
    id, ruta, herramienta, nombre, ejercicio, posicion, incluir, creado, usado, {_ESTADO} AS estado,
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


def clave_numero(numero):
    """Orden natural de números de ejercicio: 2 < 10, 3a < 3b, 4.1 < 4.10; sin número, al final."""
    if not numero:
        return (1, ())
    return (0, tuple((0, int(parte), "") if parte.isdigit() else (1, 0, parte.casefold())
                     for parte in re.findall(r"\d+|\D+", numero)))


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
        """Aplica las migraciones pendientes, cada una en su transacción, con respaldo previo."""
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version > VERSION_BASE:
            raise AlmacenFuturo("El cuaderno lo creó una versión más reciente de PyGebra.")
        if 0 < version < VERSION_BASE:
            # Una copia íntegra antes de tocar un cuaderno con datos; se conserva la primera.
            respaldo = self.archivo.with_name(f"{self.archivo.stem}.v{version}-respaldo{self.archivo.suffix}")
            if not respaldo.exists():
                with closing(sqlite3.connect(respaldo)) as copia:
                    db.backup(copia)
        for numero in range(version + 1, VERSION_BASE + 1):
            # executescript confirma lo pendiente; el BEGIN propio hace atómica cada migración.
            db.executescript(f"BEGIN;\n{MIGRACIONES[numero]}\nPRAGMA user_version = {numero};\nCOMMIT;")

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
        """Mueve las resoluciones al final del ejercicio (None las deja sueltas). No borra nada."""
        with self.conexion() as db:
            for identificador in identificadores:
                db.execute("UPDATE resoluciones SET ejercicio = ?, posicion = ? WHERE id = ?",
                           (ejercicio, self._siguiente(db, "resoluciones", {"ejercicio": ejercicio}), identificador))
            return len(identificadores)

    # ---- Orden, selección y ajustes ----

    @staticmethod
    def _siguiente(db, tabla, contenedor):
        condicion = " AND ".join(f"{campo} IS ?" for campo in contenedor)
        return db.execute(f"SELECT COALESCE(MAX(posicion), 0) + 1 FROM {tabla} WHERE {condicion}",
                          tuple(contenedor.values())).fetchone()[0]

    @staticmethod
    def _renumerar(db, tabla, ids):
        db.executemany(f"UPDATE {tabla} SET posicion = ? WHERE id = ?", [(i, ident) for i, ident in enumerate(ids, 1)])

    def mover(self, tabla, identificador, desplazamiento):
        """Sube (−1) o baja (+1) un elemento entre sus hermanos; los demás conservan su orden relativo."""
        campos = _HERMANOS[tabla]
        with self.conexion() as db:
            fila = db.execute(f"SELECT {', '.join(campos)} FROM {tabla} WHERE id = ?", (identificador,)).fetchone()
            if fila is None:
                return False
            condicion = " AND ".join(f"{campo} IS ?" for campo in campos)
            ids = [f[0] for f in db.execute(f"SELECT id FROM {tabla} WHERE {condicion} ORDER BY posicion, id", tuple(fila))]
            actual = ids.index(identificador)
            destino = min(max(actual + desplazamiento, 0), len(ids) - 1)
            ids.insert(destino, ids.pop(actual))
            self._renumerar(db, tabla, ids)
            return destino != actual

    def incluir(self, tabla, identificadores, valor):
        """Marca qué entra en el borrador del documento. Excluir nunca elimina."""
        if tabla not in _HERMANOS:
            raise ValueError(tabla)
        with self.conexion() as db:
            db.executemany(f"UPDATE {tabla} SET incluir = ? WHERE id = ?", [(int(bool(valor)), i) for i in identificadores])

    def activo(self):
        """(proyecto, ejercicio) activos mientras se navega, o (None, None)."""
        with self.conexion() as db:
            ajustes = dict(db.execute("SELECT clave, valor FROM ajustes WHERE clave LIKE 'activo_%'").fetchall())
            proyecto = db.execute("SELECT id FROM proyectos WHERE id = ?", (ajustes.get("activo_proyecto"),)).fetchone()
            ejercicio = db.execute("SELECT id FROM ejercicios WHERE id = ? AND proyecto IS ?",
                                   (ajustes.get("activo_ejercicio"), proyecto and proyecto[0])).fetchone()
        return (proyecto and proyecto[0]), (ejercicio and ejercicio[0])

    def trabajo_activo(self):
        """En una sola conexión (se pide en cada página): el proyecto activo con su progreso y sus ejercicios."""
        with self.conexion() as db:
            ajustes = dict(db.execute("SELECT clave, valor FROM ajustes WHERE clave LIKE 'activo_%'").fetchall())
            if "activo_proyecto" not in ajustes:
                return None
            proyecto = db.execute("""
                SELECT p.id, p.nombre, p.objetivo,
                       (SELECT COUNT(*) FROM ejercicios e WHERE e.proyecto = p.id) AS ejercicios,
                       (SELECT COUNT(DISTINCT r.ejercicio) FROM resoluciones r JOIN ejercicios e ON e.id = r.ejercicio
                        WHERE e.proyecto = p.id) AS resueltos
                FROM proyectos p WHERE p.id = ?""", (ajustes["activo_proyecto"],)).fetchone()
            if proyecto is None:
                return None
            ejercicios = [dict(f) for f in db.execute(
                "SELECT id, nombre, numero, proyecto, seccion FROM ejercicios WHERE proyecto = ? ORDER BY posicion, id",
                (proyecto["id"],))]
        ejercicio = next((e for e in ejercicios if str(e["id"]) == ajustes.get("activo_ejercicio")), None)
        return dict(proyecto), ejercicios, ejercicio

    def activar(self, proyecto, ejercicio=None):
        with self.conexion() as db:
            for clave, valor in (("activo_proyecto", proyecto), ("activo_ejercicio", ejercicio)):
                if valor is None:
                    db.execute("DELETE FROM ajustes WHERE clave = ?", (clave,))
                else:
                    db.execute("INSERT OR REPLACE INTO ajustes (clave, valor) VALUES (?, ?)", (clave, str(valor)))

    # ---- Proyectos y secciones ----

    def proyectos(self):
        """Cada proyecto con sus ejercicios, cuántos tienen ya una resolución y su última actividad."""
        with self.conexion() as db:
            return [dict(f) for f in db.execute("""
                SELECT p.id, p.nombre, p.objetivo, p.creado,
                       COUNT(DISTINCT e.id) AS ejercicios,
                       COUNT(DISTINCT r.ejercicio) AS resueltos,
                       COALESCE(MAX(r.usado), p.creado) AS ultima
                FROM proyectos p
                LEFT JOIN ejercicios e ON e.proyecto = p.id
                LEFT JOIN resoluciones r ON r.ejercicio = e.id
                GROUP BY p.id ORDER BY ultima DESC, p.id DESC""")]

    def crear_proyecto(self, nombre, objetivo=None):
        with self.conexion() as db:
            return db.execute("INSERT INTO proyectos (nombre, objetivo, creado) VALUES (?, ?, ?)",
                              (nombre[:MAX_NOMBRE], objetivo, ahora())).lastrowid

    def editar_proyecto(self, identificador, nombre, objetivo):
        with self.conexion() as db:
            return db.execute("UPDATE proyectos SET nombre = ?, objetivo = ? WHERE id = ?",
                              (nombre[:MAX_NOMBRE], objetivo, identificador)).rowcount

    def eliminar_proyecto(self, identificador):
        """Quita el proyecto y sus secciones; sus ejercicios y resoluciones siguen en el cuaderno."""
        with self.conexion() as db:
            db.execute("UPDATE ejercicios SET proyecto = NULL, seccion = NULL WHERE proyecto = ?", (identificador,))
            return db.execute("DELETE FROM proyectos WHERE id = ?", (identificador,)).rowcount

    def secciones(self, proyecto):
        with self.conexion() as db:
            return [dict(f) for f in db.execute(
                "SELECT id, proyecto, titulo, posicion, incluir FROM secciones WHERE proyecto = ? ORDER BY posicion, id",
                (proyecto,))]

    def crear_seccion(self, proyecto, titulo):
        with self.conexion() as db:
            return db.execute("INSERT INTO secciones (proyecto, titulo, posicion) VALUES (?, ?, ?)",
                              (proyecto, titulo[:MAX_NOMBRE], self._siguiente(db, "secciones", {"proyecto": proyecto}))).lastrowid

    def editar_seccion(self, identificador, titulo):
        with self.conexion() as db:
            return db.execute("UPDATE secciones SET titulo = ? WHERE id = ?", (titulo[:MAX_NOMBRE], identificador)).rowcount

    def eliminar_seccion(self, identificador):
        """Quita la sección; sus ejercicios pasan al final del proyecto, sin sección."""
        with self.conexion() as db:
            fila = db.execute("SELECT proyecto FROM secciones WHERE id = ?", (identificador,)).fetchone()
            if fila is None:
                return 0
            for (ejercicio,) in db.execute("SELECT id FROM ejercicios WHERE seccion = ? ORDER BY posicion, id",
                                           (identificador,)).fetchall():
                db.execute("UPDATE ejercicios SET seccion = NULL, posicion = ? WHERE id = ?",
                           (self._siguiente(db, "ejercicios", {"proyecto": fila[0], "seccion": None}), ejercicio))
            return db.execute("DELETE FROM secciones WHERE id = ?", (identificador,)).rowcount

    # ---- Ejercicios ----

    def ejercicios(self, proyecto=...):
        """Todos los ejercicios, o los de un proyecto (None: los independientes), en su orden."""
        consulta = "SELECT id, nombre, numero, enunciado, proyecto, seccion, posicion, incluir, creado FROM ejercicios"
        with self.conexion() as db:
            if proyecto is ...:
                filas = db.execute(f"{consulta} ORDER BY proyecto, posicion, id")
            else:
                filas = db.execute(f"{consulta} WHERE proyecto IS ? ORDER BY posicion, id", (proyecto,))
            return [dict(f) for f in filas]

    def crear_ejercicio(self, nombre, proyecto=None, seccion=None, numero=None, enunciado=None):
        with self.conexion() as db:
            posicion = self._siguiente(db, "ejercicios", {"proyecto": proyecto, "seccion": seccion})
            return db.execute(
                "INSERT INTO ejercicios (nombre, proyecto, seccion, numero, enunciado, posicion, creado)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombre[:MAX_NOMBRE], proyecto, seccion, numero, enunciado, posicion, ahora())).lastrowid

    def crear_ejercicios(self, proyecto, numeros, seccion=None):
        """Ejercicios vacíos numerados, preparados antes de resolverlos (p. ej. del 1 al 64)."""
        with self.conexion() as db:
            existentes = {f[0] for f in db.execute("SELECT numero FROM ejercicios WHERE proyecto = ?", (proyecto,))}
            nuevos = [n for n in numeros if n not in existentes]
            posicion = self._siguiente(db, "ejercicios", {"proyecto": proyecto, "seccion": seccion})
            momento = ahora()
            db.executemany(
                "INSERT INTO ejercicios (nombre, proyecto, seccion, numero, posicion, creado) VALUES ('', ?, ?, ?, ?, ?)",
                [(proyecto, seccion, numero, posicion + i, momento) for i, numero in enumerate(nuevos)])
            return len(nuevos)

    def editar_ejercicio(self, identificador, *, nombre, numero, enunciado):
        with self.conexion() as db:
            return db.execute("UPDATE ejercicios SET nombre = ?, numero = ?, enunciado = ? WHERE id = ?",
                              (nombre[:MAX_NOMBRE], numero, enunciado, identificador)).rowcount

    def ubicar_ejercicios(self, identificadores, proyecto, seccion=None):
        """Lleva ejercicios a un proyecto o sección (None: independientes), al final y con sus resoluciones."""
        with self.conexion() as db:
            for identificador in identificadores:
                db.execute("UPDATE ejercicios SET proyecto = ?, seccion = ?, posicion = ? WHERE id = ?",
                           (proyecto, seccion, self._siguiente(db, "ejercicios", {"proyecto": proyecto, "seccion": seccion}),
                            identificador))
            if proyecto is None:
                db.execute("DELETE FROM ajustes WHERE clave = 'activo_ejercicio' AND valor IN ({})".format(
                    ",".join("?" * len(identificadores))), [str(i) for i in identificadores])

    def ordenar_por_numero(self, proyecto):
        """Reordena cada sección del proyecto por número natural; sin número, al final y en su orden."""
        with self.conexion() as db:
            filas = db.execute("SELECT id, seccion, numero FROM ejercicios WHERE proyecto = ? ORDER BY posicion, id",
                               (proyecto,)).fetchall()
            for seccion in {f["seccion"] for f in filas}:
                propias = [f for f in filas if f["seccion"] == seccion]
                self._renumerar(db, "ejercicios", [f["id"] for f in sorted(propias, key=lambda f: clave_numero(f["numero"]))])

    def existe_ejercicio(self, identificador):
        with self.conexion() as db:
            return db.execute("SELECT 1 FROM ejercicios WHERE id = ?", (identificador,)).fetchone() is not None

    def renombrar_ejercicio(self, identificador, nombre):  # Compatibilidad con el cuaderno v1.
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
