(function () {
  const board = document.getElementById("board");
  if (!board) return;

  const CLICK_THRESHOLD = 6;

  function topZ() {
    let max = 0;
    board.querySelectorAll(".card").forEach((c) => {
      max = Math.max(max, parseInt(c.style.zIndex || "0", 10));
    });
    return max;
  }

  function savePosition(card) {
    const id = card.dataset.id;
    const x = parseInt(card.style.left, 10);
    const y = parseInt(card.style.top, 10);
    fetch(`/areas/${id}/position`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x, y }),
    });
  }

  board.querySelectorAll(".card").forEach((card) => {
    let dragging = false;
    let startX = 0;
    let startY = 0;
    let cardStartLeft = 0;
    let cardStartTop = 0;
    let moved = 0;

    card.addEventListener("pointerdown", (e) => {
      dragging = true;
      moved = 0;
      startX = e.clientX;
      startY = e.clientY;
      cardStartLeft = parseInt(card.style.left || "0", 10);
      cardStartTop = parseInt(card.style.top || "0", 10);
      card.style.zIndex = topZ() + 1;
      card.classList.add("dragging");
      card.setPointerCapture(e.pointerId);
    });

    card.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      moved = Math.max(moved, Math.abs(dx), Math.abs(dy));
      card.style.left = `${Math.max(0, cardStartLeft + dx)}px`;
      card.style.top = `${Math.max(0, cardStartTop + dy)}px`;
    });

    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      card.classList.remove("dragging");
      if (moved < CLICK_THRESHOLD) {
        window.location.href = card.dataset.href;
      } else {
        savePosition(card);
      }
    }

    card.addEventListener("pointerup", endDrag);
    card.addEventListener("pointercancel", endDrag);
  });

  const tidyBtn = document.getElementById("tidy-btn");
  if (tidyBtn) {
    tidyBtn.addEventListener("click", () => {
      const pieceId = board.dataset.pieceId;
      const cards = Array.from(board.querySelectorAll(".card"));

      const MARGIN = 16;
      const GAP = 14;
      const CARD_W = 170;
      const CARD_H = 116;
      const boardWidth = board.clientWidth || 340;
      const cols = Math.max(1, Math.floor((boardWidth - MARGIN * 2 + GAP) / (CARD_W + GAP)));

      const positions = cards.map((card, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        const x = MARGIN + col * (CARD_W + GAP);
        const y = MARGIN + row * (CARD_H + GAP);
        card.style.left = `${x}px`;
        card.style.top = `${y}px`;
        card.style.zIndex = i;
        return { id: parseInt(card.dataset.id, 10), x, y };
      });

      fetch(`/pieces/${pieceId}/tidy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ positions }),
      });
    });
  }
})();
