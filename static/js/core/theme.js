function update_theme_button()
{
    const button = document.querySelector(".config-theme-toggle i")
    if (!button)
        return

    const theme = get_theme()

    const icons = {
        dark: "moon",
        light: "sun",
        system: "desktop"
    }

    button.innerHTML = `<i class="fa-solid fa-${icons[theme]}"></i>`
    button.title = `${theme[0].toUpperCase()}${theme.slice(1)} Theme`
}
function get_theme() {
    return localStorage.getItem("theme") || "system"
}

function set_theme(theme) {
    localStorage.setItem("theme", theme)
    apply_theme()
}

function get_effective_theme() {
    if (get_theme() !== "system")
        return get_theme()

    return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
}

function apply_theme() {
    document.documentElement.setAttribute(
        "data-theme",
        get_effective_theme()
    )

    update_theme_button()
}

function cycle_theme() {
    const themes = ["dark", "light", "system"]
    const current = themes.indexOf(get_theme())

    set_theme(
        themes[(current + 1) % themes.length]
    )
}

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (get_theme() === "system")
            apply_theme()
    })

apply_theme()