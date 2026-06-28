function format_duration(sec) {
    if (!sec)
        return ""

    if (sec < 1)
        return `${Math.round(sec * 1000)}ms`

    if (sec < 60)
        return `${sec.toFixed(1)}s`

    const min = Math.floor(sec / 60)
    const rem = Math.floor(sec % 60)

    return `${min}m ${rem}s`
}
