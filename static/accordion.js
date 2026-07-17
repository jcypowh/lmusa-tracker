(function () {
  const accordion = document.getElementById("accordion");
  if (!accordion) return;

  accordion.querySelectorAll(".acc-header").forEach((header) => {
    header.addEventListener("click", () => {
      const body = document.getElementById(header.dataset.target);
      const isOpen = header.getAttribute("aria-expanded") === "true";
      header.setAttribute("aria-expanded", String(!isOpen));
      header.classList.toggle("open", !isOpen);
      if (body) body.hidden = isOpen;
    });
  });

  function hexToRgb(hex) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
    const num = parseInt(hex, 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
  }

  function mixWithWhite(hex, percent) {
    const t = Math.max(0, Math.min(100, percent)) / 100;
    const [r, g, b] = hexToRgb(hex);
    const mix = (c) => Math.round(255 + (c - 255) * t);
    return `rgb(${mix(r)}, ${mix(g)}, ${mix(b)})`;
  }

  accordion.querySelectorAll(".acc-slider").forEach((slider) => {
    const areaId = slider.dataset.areaId;
    const pieceColor = slider.dataset.color;
    const valueLabel = slider.parentElement.querySelector(".acc-slider-value");
    const header = document.querySelector(
      `.acc-header[data-target="acc-body-${areaId}"]`
    );
    const percentBadge = header ? header.querySelector(".acc-percent") : null;

    slider.addEventListener("input", () => {
      if (valueLabel) valueLabel.textContent = slider.value;
      if (percentBadge) percentBadge.textContent = `${slider.value}%`;
      if (header) header.style.background = mixWithWhite(pieceColor, parseInt(slider.value, 10));
    });

    slider.addEventListener("change", () => {
      fetch(`/areas/${areaId}/percent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ percent: parseInt(slider.value, 10) }),
      });
    });
  });
})();
