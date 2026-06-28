function render_badge(icon, text, cls = "") {
    return `
        <span class="environment-badge ${cls}">
            <i class="${icon}"></i>
            ${text}
        </span>
    `
}
