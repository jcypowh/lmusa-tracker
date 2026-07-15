(function () {
  const slider = document.getElementById("percent-slider");
  if (!slider) return;

  const valueLabel = document.getElementById("percent-value");
  const swatch = document.getElementById("percent-swatch");
  const areaId = slider.dataset.areaId;
  const pieceColor = slider.dataset.color;

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

  slider.addEventListener("input", () => {
    if (valueLabel) valueLabel.textContent = slider.value;
    if (swatch) swatch.style.background = mixWithWhite(pieceColor, parseInt(slider.value, 10));
  });

  slider.addEventListener("change", () => {
    fetch(`/areas/${areaId}/percent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ percent: parseInt(slider.value, 10) }),
    });
  });
})();
