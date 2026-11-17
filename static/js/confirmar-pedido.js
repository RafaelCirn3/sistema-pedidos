(() => {
  const dialog = document.getElementById("confirmar-pedido");
  if (!dialog || typeof dialog.showModal !== "function") return;
  const prato = document.getElementById("confirmar-prato");
  const opcoes = document.getElementById("confirmar-opcoes");
  const enviar = document.getElementById("enviar-pedido");
  let formulario = null;

  document.querySelectorAll(".pedido-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.elements.confirmar.value === "sim") return;
      event.preventDefault();
      if (dialog.open) return;
      formulario = form;
      prato.textContent = form.dataset.prato;
      const selecionadas = Array.from(form.querySelectorAll('input[name="opcoes"]:checked'));
      opcoes.replaceChildren();
      const nomes = selecionadas.map((input) => input.closest("label").textContent.trim());
      if (!nomes.length) nomes.push("Nenhuma opção adicional");
      nomes.forEach((nome) => {
        const item = document.createElement("li");
        item.textContent = nome;
        opcoes.appendChild(item);
      });
      enviar.disabled = false;
      dialog.showModal();
    });
  });
  document.getElementById("voltar-pedido").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => { formulario = null; });
  enviar.addEventListener("click", () => {
    if (!formulario || enviar.disabled) return;
    enviar.disabled = true;
    formulario.elements.confirmar.value = "sim";
    formulario.requestSubmit();
  });
})();
