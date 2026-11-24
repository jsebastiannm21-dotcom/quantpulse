// sitio.js - Clase gratis (el quiz aparece al tocar «Terminé el tema», igual que en la app) y botón «Copiar».
(function () {
  const termine = document.getElementById("termine");
  const quiz = document.getElementById("quiz");
  if (termine && quiz) {
    termine.addEventListener("click", () => {
      quiz.hidden = false;
      termine.hidden = true;
      quiz.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    quiz.addEventListener("submit", (ev) => {
      ev.preventDefault();
      let bien = 0, completas = true;
      quiz.querySelectorAll(".pregunta").forEach((p) => {
        const marcada = p.querySelector("input:checked");
        const res = p.querySelector(".resultado");
        if (!marcada) { completas = false; res.hidden = false; res.className = "resultado mal"; res.textContent = "Responde esta pregunta."; return; }
        const ok = marcada.value === p.dataset.correcta;
        bien += ok ? 1 : 0;
        res.hidden = false;
        res.className = "resultado " + (ok ? "bien" : "mal");
        res.textContent = (ok ? "Correcto: " : "Incorrecto: ") + p.dataset.explicacion;
      });
      const total = document.getElementById("total");
      total.hidden = false;
      total.textContent = completas ? (bien >= 2 ? `¡Aprobado! ${bien} de 3.` : `${bien} de 3. Repasa el tema y vuelve a intentarlo.`)
                                    : "Responde las 3 preguntas.";
    });
  }
  document.querySelectorAll(".copiar").forEach((b) => {
    b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(b.dataset.copiar); b.textContent = "Copiado"; }
      catch (e) { const r = document.createRange(); r.selectNodeContents(b.previousElementSibling);
        const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = "Selecciónalo y cópialo"; }
    });
  });
})();
