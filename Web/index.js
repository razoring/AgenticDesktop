lucide.createIcons();

// Source - https://stackoverflow.com/a/25621277
// Posted by DreamTeK, modified by community. See post 'Timeline' for change history
// Retrieved 2026-07-17, License - CC BY-SA 4.0

document.querySelectorAll("textarea").forEach(function (textarea) {
    const resize = () => {
        textarea.style.height = "0px";
        textarea.style.height = textarea.scrollHeight + "px";
    };

    textarea.addEventListener("input", resize);
    
    // Initial resize
    textarea.style.overflowY = "hidden";
    resize();
});