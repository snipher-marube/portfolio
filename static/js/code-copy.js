// static/js/code-copy.js
document.addEventListener('DOMContentLoaded', function() {
    // Process all code blocks
    document.querySelectorAll('pre code').forEach(function(codeBlock) {
        const container = document.createElement('div');
        container.className = 'code-container';
        
        const header = document.createElement('div');
        header.className = 'code-header';
        
        const language = document.createElement('div');
        language.className = 'code-language';
        
        // Detect language from class
        const langClass = Array.from(codeBlock.classList).find(cls => cls.startsWith('language-'));
        const langName = langClass ? langClass.replace('language-', '').toUpperCase() : 'CODE';
        
        language.innerHTML = `
            <span class="language-dot"></span>
            <span class="language-name">${langName}</span>
        `;
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-btn';
        copyButton.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            Copy
        `;
        
        copyButton.addEventListener('click', function() {
            const code = codeBlock.textContent;
            navigator.clipboard.writeText(code).then(function() {
                // Success feedback
                const originalText = copyButton.innerHTML;
                copyButton.classList.add('copied');
                
                setTimeout(function() {
                    copyButton.classList.remove('copied');
                    copyButton.innerHTML = originalText;
                }, 2000);
            }).catch(function(err) {
                console.error('Failed to copy code: ', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = code;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                copyButton.classList.add('copied');
                setTimeout(function() {
                    copyButton.classList.remove('copied');
                }, 2000);
            });
        });
        
        header.appendChild(language);
        header.appendChild(copyButton);
        
        const pre = codeBlock.parentElement;
        container.appendChild(header);
        container.appendChild(pre);
        
        pre.parentNode.insertBefore(container, pre);
        container.appendChild(pre);
    });
});