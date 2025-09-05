// Custom prompt replacement
(function() {
  let modal = null;
  let resolvePromise = null;
  let inputEl, okBtn, cancelBtn;

  function createModal() {
    const modalElement = document.createElement('div');
    modalElement.id = 'custom-prompt-overlay';
    modalElement.className = 'fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 hidden';
    
    modalElement.innerHTML = `
      <div id="custom-prompt-panel" class="bg-white/60 backdrop-blur-xl border border-white/20 w-full max-w-md rounded-2xl shadow-2xl p-6 md:p-8">
        <h3 id="custom-prompt-title" class="text-2xl font-bold font-lalezar text-purple-700 mb-2 text-center"></h3>
        <p id="custom-prompt-message" class="text-slate-700 mb-6 text-center whitespace-pre-wrap"></p>
        <input type="text" id="custom-prompt-input" class="w-full bg-white/50 border border-slate-300/70 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition mb-6">
        <div class="flex justify-end gap-3">
            <button id="custom-prompt-cancel" class="text-slate-600 font-semibold px-5 py-2.5 rounded-lg hover:bg-slate-100 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400">
                Cancel
            </button>
            <button id="custom-prompt-ok" class="bg-purple-600 text-white px-6 py-2.5 rounded-lg hover:bg-purple-700 font-semibold transition shadow-md hover:shadow-lg transform hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2">
                OK
            </button>
        </div>
      </div>`;
    
    document.body.appendChild(modalElement);

    inputEl = modalElement.querySelector('#custom-prompt-input');
    okBtn = modalElement.querySelector('#custom-prompt-ok');
    cancelBtn = modalElement.querySelector('#custom-prompt-cancel');

    const close = (value) => {
        modalElement.classList.add('hidden');
        if (resolvePromise) {
            resolvePromise(value);
            resolvePromise = null;
        }
    };
    
    okBtn.addEventListener('click', () => close(inputEl.value));
    cancelBtn.addEventListener('click', () => close(null));
    modalElement.addEventListener('click', (e) => {
        if (e.target.id === 'custom-prompt-overlay') {
            close(null);
        }
    });
    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            close(inputEl.value);
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape" && !modalElement.classList.contains('hidden')) {
            close(null);
        }
    });

    return modalElement;
  }

  window.prompt = function(message, defaultValue = '', title = 'Input Required') {
    if (!modal) {
      modal = createModal();
    }

    modal.querySelector('#custom-prompt-title').textContent = title;
    modal.querySelector('#custom-prompt-message').textContent = message;
    modal.querySelector('#custom-prompt-input').value = defaultValue;

    modal.classList.remove('hidden');
    setTimeout(() => { inputEl.focus(); inputEl.select(); }, 50);

    return new Promise(resolve => {
      resolvePromise = resolve;
    });
  };
})();