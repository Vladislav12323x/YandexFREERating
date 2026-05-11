document.querySelectorAll('.copy-link-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const url = this.getAttribute('data-url');

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(url).then(() => {
                showCopyFeedback(this, '✓ Скопировано!');
            });
        }
        else {
            const textarea = document.createElement("textarea");
            textarea.value = url;
            textarea.style.position = "fixed";
            textarea.style.left = "-9999px";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            try {
                document.execCommand('copy');
                showCopyFeedback(this, '✓ Скопировано!');
            } catch (err) {
                prompt("Нажмите Ctrl+C, чтобы скопировать ссылку:", url);
            }
            document.body.removeChild(textarea);
        }
    });
});

function showCopyFeedback(btn, message) {
    const originalHTML = btn.innerHTML;
    btn.innerHTML = `<span class="text-success fw-bold">${message}</span>`;
    btn.classList.replace('btn-outline-primary', 'btn-success');
    btn.disabled = true;
    
    setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.classList.replace('btn-success', 'btn-outline-primary');
        btn.disabled = false;
    }, 2000);
}