(() => {
    "use strict";

    const resultado = document.querySelector("[data-resultado]");
    const form = document.querySelector("[data-entrada-calculo]");
    if (!resultado || !form) return;
    const aviso = document.createElement("p");
    aviso.className = "result-notice";
    aviso.setAttribute("role", "status");
    resultado.querySelector(".results-heading").after(aviso);
    // Solo datos enviados al cálculo; los controles de presentación quedan fuera.
    const firma = () => JSON.stringify([...new FormData(form)].filter(([nombre]) =>
        !["csrfmiddlewaretoken", "confirmacion"].includes(nombre)));
    const entrada = firma();
    function actualizar() {
        if (resultado.dataset.resultado === "desactualizado" || firma() === entrada) return;
        resultado.dataset.resultado = "desactualizado";
        aviso.textContent = "Cambiaste los datos. Este resultado corresponde a la entrada anterior. Vuelve a calcular para actualizarlo.";
    }
    ["input", "change", "entrada-cambiada"].forEach(tipo => form.addEventListener(tipo, actualizar));
})();
