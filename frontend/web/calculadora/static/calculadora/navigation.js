(() => {
    "use strict";

    const button = document.getElementById("navigation-toggle");
    const navigation = document.getElementById("navegacion-principal");
    if (!button || !navigation) return;

    const mobile = window.matchMedia("(max-width: 900px)");
    function setExpanded(expanded) {
        button.setAttribute("aria-expanded", String(expanded));
        navigation.hidden = mobile.matches && !expanded;
    }
    function syncLayout() {
        const focusWasInNavigation = navigation.contains(document.activeElement);
        const focusWasOnButton = document.activeElement === button;
        button.hidden = !mobile.matches;
        setExpanded(!mobile.matches);
        if (mobile.matches && focusWasInNavigation) button.focus();
        if (!mobile.matches && focusWasOnButton) navigation.querySelector("a").focus();
    }
    button.addEventListener("click", () => {
        setExpanded(button.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && mobile.matches && !navigation.hidden) {
            setExpanded(false);
            button.focus();
        }
    });
    mobile.addEventListener("change", syncLayout);
    syncLayout();
})();
