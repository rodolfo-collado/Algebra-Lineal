// Ejecuta runners DOM (tests/*_browser.py) en Chrome o Edge sin ventana, por CDP y sin
// dependencias: Node 22 o posterior (WebSocket y fetch globales).
//
//   uv run --locked node tests/navegador.mjs                 # la selección de CI
//   uv run --locked node tests/navegador.mjs secante conjuntos
//
// Cada runner arranca su servidor (python -m tests.<nombre>_browser), se abre en un perfil
// nuevo con el foco emulado y termina cuando #total muestra «a/b». Falla si a ≠ b, si se
// agota su tiempo o si el servidor muere. Ante un fallo deja en NAVEGADOR_SALIDA (por
// defecto build/navegador) las filas, la consola, la salida del servidor y una captura.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

// Selección de CI: un runner por área prioritaria (ver docs/pruebas.md#navegador-en-ci).
const SELECCION = [
    "escritorio",   // navegación: barra lateral, rutas y teclado global
    "buscador",     // navegación: buscador, áreas, explorador y música
    "entradas",     // cuadrículas: construcción y flechas celda a celda
    "teclado",      // teclado matemático
    "operandos",    // edición matricial con varios operandos
    "claridad",     // formato numérico Exacto/Decimal
    "biseccion",    // gráfica de raíces frente al JSON
    "secante",
    "iterativos",   // Jacobi y Gauss-Seidel
    "conjuntos",
    "resoluciones", // cuaderno: guardar, reabrir, agrupar y los cinco estilos
];
const LIMITE_MS = Number(process.env.NAVEGADOR_LIMITE_MS || 240000);
const SALIDA = path.resolve(process.env.NAVEGADOR_SALIDA || "build/navegador");
const dormir = ms => new Promise(r => setTimeout(r, ms));

function navegador() {
    const candidatos = [
        process.env.NAVEGADOR,
        "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
    ];
    const encontrado = candidatos.find(ruta => ruta && fs.existsSync(ruta));
    if (!encontrado) throw new Error("No hay Chrome ni Edge; indica la ruta en NAVEGADOR.");
    return encontrado;
}

// El servidor anuncia su URL en la primera línea («…: http://127.0.0.1:8902/__pruebas/»).
function arrancarServidor(nombre, registro) {
    const python = process.env.PYTHON || (process.platform === "win32" ? "python.exe" : "python");
    const servidor = spawn(python, ["-u", "-m", `tests.${nombre}_browser`], { stdio: ["ignore", "pipe", "pipe"] });
    const url = new Promise((resolver, rechazar) => {
        const leer = trozo => {
            registro.push(trozo.toString());
            const encontrada = /http:\/\/127\.0\.0\.1:\d+\/\S*/.exec(registro.join(""));
            if (encontrada) resolver(encontrada[0]);
        };
        servidor.stdout.on("data", leer);
        servidor.stderr.on("data", leer);
        servidor.on("exit", codigo => rechazar(new Error(`El servidor terminó con código ${codigo} antes de anunciar su URL.`)));
    });
    return { servidor, url };
}

async function conectar(binario, perfil) {
    const argumentos = ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${perfil}`,
        "--no-first-run", "--no-default-browser-check", "--disable-gpu", "--window-size=1400,1000",
        // Sin ventana no hay gesto de usuario: AudioContext.resume() quedaría pendiente para siempre.
        "--autoplay-policy=no-user-gesture-required", "about:blank"];
    // Ubuntu 24.04 restringe los espacios de nombres que usa el sandbox de Chrome; solo se
    // cargan páginas de 127.0.0.1 servidas por el propio runner.
    if (process.platform === "linux") argumentos.unshift("--no-sandbox");
    const proceso = spawn(binario, argumentos, { stdio: ["ignore", "ignore", "pipe"] });
    const errores = [];
    proceso.stderr.on("data", trozo => errores.push(trozo.toString()));
    const puertoArchivo = path.join(perfil, "DevToolsActivePort");
    // El primer arranque en frío de Chrome en un runner nuevo pasó de 15 s; se espera a que
    // publique su puerto, no un tiempo fijo, y se deja de esperar si el proceso muere.
    const fin = Date.now() + 60000;
    let destino;
    while (!destino && Date.now() < fin && proceso.exitCode === null) {
        await dormir(100);
        try {
            const puerto = fs.readFileSync(puertoArchivo, "utf8").split("\n")[0];
            const paginas = await (await fetch(`http://127.0.0.1:${puerto}/json/list`)).json();
            destino = paginas.find(p => p.type === "page");
        } catch { /* Todavía arrancando (o EBUSY en Windows). */ }
    }
    if (!destino) {
        const estado = proceso.exitCode === null ? "sigue sin responder tras 60 s" : `terminó con código ${proceso.exitCode}`;
        proceso.kill();
        throw new Error(`El navegador no abrió el puerto de depuración: ${estado}. ${errores.join("").trim().slice(-800)}`);
    }
    const ws = new WebSocket(destino.webSocketDebuggerUrl);
    await new Promise((ok, mal) => { ws.onopen = ok; ws.onerror = mal; });
    let id = 0;
    const pendientes = new Map();
    const eventos = [];
    ws.onmessage = mensaje => {
        const datos = JSON.parse(mensaje.data);
        if (datos.id && pendientes.has(datos.id)) {
            pendientes.get(datos.id)(datos);
            pendientes.delete(datos.id);
        } else if (datos.method) eventos.push(datos);
    };
    const enviar = (method, params = {}) => new Promise((ok, mal) => {
        pendientes.set(++id, datos => (datos.error ? mal(new Error(datos.error.message)) : ok(datos.result)));
        ws.send(JSON.stringify({ id, method, params }));
    });
    return { proceso, ws, enviar, eventos };
}

function consola(eventos) {
    return eventos.flatMap(({ method, params }) => {
        if (method === "Runtime.exceptionThrown") {
            const d = params.exceptionDetails;
            return [`excepción: ${d.exception?.description || d.text} (${d.url || ""}:${d.lineNumber})`];
        }
        if (method === "Runtime.consoleAPICalled" && ["error", "warning", "assert"].includes(params.type)) {
            return [`console.${params.type}: ${params.args.map(a => a.value ?? a.description ?? "").join(" ")}`];
        }
        if (method === "Log.entryAdded" && params.entry.level === "error") return [`log: ${params.entry.text} ${params.entry.url || ""}`];
        return [];
    });
}

async function ejecutar(nombre, binario) {
    const inicio = Date.now();
    const registro = [];
    const perfil = fs.mkdtempSync(path.join(os.tmpdir(), "pygebra-navegador-"));
    const { servidor, url } = arrancarServidor(nombre, registro);
    let cdp;
    const informe = { nombre, ok: false, total: "", filas: [], consola: [], motivo: "" };
    try {
        const direccion = await Promise.race([url, dormir(30000).then(() => { throw new Error("El servidor no anunció su URL en 30 s."); })]);
        cdp = await conectar(binario, perfil);
        const { enviar } = cdp;
        await enviar("Runtime.enable");
        await enviar("Log.enable");
        await enviar("Page.enable");
        // Sin ventana el documento no tiene foco: los casos de foco y teclado lo necesitan.
        await enviar("Emulation.setFocusEmulationEnabled", { enabled: true });
        await enviar("Page.navigate", { url: direccion });
        const leer = async expresion => (await enviar("Runtime.evaluate", { expression: expresion, returnByValue: true })).result.value;
        const fin = inicio + LIMITE_MS;
        // Si el puerto ya estaba ocupado (p. ej. un servidor huérfano con código viejo), el
        // nuevo muere al enlazarlo: se informa en lugar de probar contra el otro proceso.
        const servidorVivo = () => servidor.exitCode === null && servidor.signalCode === null;
        while (Date.now() < fin && servidorVivo()) {
            informe.total = (await leer("document.getElementById('total')?.textContent || ''")) || "";
            if (/\d+\s*\/\s*\d+/.test(informe.total)) break;
            await dormir(500);
        }
        informe.filas = (await leer("[...document.querySelectorAll('#resultados li')].map(li => li.textContent.trim())")) || [];
        const cuenta = /(\d+)\s*\/\s*(\d+)/.exec(informe.total);
        if (!servidorVivo()) informe.motivo = "el servidor terminó durante la ejecución";
        else if (!cuenta) informe.motivo = `sin resultado tras ${LIMITE_MS / 1000} s (${informe.filas.length} filas escritas)`;
        else if (cuenta[1] !== cuenta[2] || cuenta[2] === "0") informe.motivo = "hay casos fallidos";
        informe.ok = !informe.motivo;
        if (!informe.ok) {
            const captura = await enviar("Page.captureScreenshot", { format: "png", captureBeyondViewport: false }).catch(() => null);
            fs.mkdirSync(SALIDA, { recursive: true });
            if (captura) fs.writeFileSync(path.join(SALIDA, `${nombre}.png`), Buffer.from(captura.data, "base64"));
        }
    } catch (error) {
        informe.motivo = error.message;
    } finally {
        informe.segundos = (Date.now() - inicio) / 1000;
        if (cdp) {
            informe.consola = consola(cdp.eventos);
            cdp.ws.close();
            cdp.proceso.kill();
        }
        servidor.kill();
        if (!informe.ok) {
            fs.mkdirSync(SALIDA, { recursive: true });
            fs.writeFileSync(path.join(SALIDA, `${nombre}.txt`), [
                `${nombre}: ${informe.motivo}`, `total: ${informe.total}`, "", "## Casos", ...informe.filas,
                "", "## Consola", ...informe.consola, "", "## Servidor", registro.join(""),
            ].join("\n"));
        }
        // En Windows el perfil sigue bloqueado un instante tras cerrar el navegador (EBUSY).
        // Es un temporal: si no se puede borrar, no debe tumbar los runners siguientes.
        setTimeout(() => {
            try { fs.rmSync(perfil, { recursive: true, force: true, maxRetries: 5 }); } catch { /* Queda en %TEMP%. */ }
        }, 1000);
    }
    return informe;
}

const nombres = process.argv.slice(2).length ? process.argv.slice(2) : SELECCION;
const binario = navegador();
const informes = [];
for (const nombre of nombres) {
    const informe = await ejecutar(nombre, binario);
    informes.push(informe);
    const marca = informe.ok ? "OK   " : "FALLO";
    console.log(`${marca} ${nombre.padEnd(16)} ${informe.total.padEnd(34)} ${informe.segundos.toFixed(1)} s`);
    if (!informe.ok) {
        console.log(`      motivo: ${informe.motivo}`);
        for (const fila of informe.filas.filter(f => !/^(OK|PASS|✓)\b/i.test(f))) console.log(`      ${fila}`);
        for (const linea of informe.consola.slice(0, 20)) console.log(`      ${linea}`);
    }
}
const resumen = process.env.GITHUB_STEP_SUMMARY;
if (resumen) {
    fs.appendFileSync(resumen, ["| Runner | Resultado | Tiempo |", "|---|---|---|",
        ...informes.map(i => `| ${i.nombre} | ${i.ok ? "✅" : "❌"} ${i.total || i.motivo} | ${i.segundos.toFixed(1)} s |`), ""].join("\n"));
}
const fallidos = informes.filter(i => !i.ok).map(i => i.nombre);
console.log(fallidos.length ? `Fallaron: ${fallidos.join(", ")} (detalles en ${SALIDA})` : `${informes.length} runners correctos.`);
process.exit(fallidos.length ? 1 : 0);
