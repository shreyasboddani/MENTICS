// Custom alert replacement
(function() {
  let modal = null;

  function createModal() {
    const modalElement = document.createElement('div');
    modalElement.id = 'custom-alert-overlay';
    modalElement.className = 'fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 hidden';
    
    modalElement.innerHTML = `
      <div id="custom-alert-panel" class="bg-white/60 backdrop-blur-xl border border-white/20 w-full max-w-md rounded-2xl shadow-2xl p-6 md:p-8 text-center">
        <h3 id="custom-alert-title" class="text-2xl font-bold font-lalezar text-purple-700 mb-4"></h3>
        <p id="custom-alert-message" class="text-slate-700 mb-6"></p>
        <div class="flex justify-center">
            <button id="custom-alert-ok" class="bg-purple-600 text-white px-6 py-2.5 rounded-lg hover:bg-purple-700 font-semibold transition shadow-md hover:shadow-lg transform hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2">
                OK
            </button>
        </div>
      </div>`;
    
    document.body.appendChild(modalElement);

    const okBtn = modalElement.querySelector('#custom-alert-ok');
    const close = () => modalElement.classList.add('hidden');
    
    okBtn.addEventListener('click', close);
    modalElement.addEventListener('click', (e) => {
        if (e.target === modalElement) {
            close();
        }
    });

    return modalElement;
  }

  window.alert = function(message, title = 'Notification') {
    if (!modal) {
      modal = createModal();
    }

    const titleEl = modal.querySelector('#custom-alert-title');
    const messageEl = modal.querySelector('#custom-alert-message');
    
    titleEl.textContent = title;
    messageEl.innerHTML = message; // Use innerHTML to allow for simple formatting

    modal.classList.remove('hidden');
  };
})();
