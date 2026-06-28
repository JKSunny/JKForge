window.current_run_environment = null
window.current_environments = []

window.activeCommandEnvId = null
window.activeCommandRunId = null

window.active_requests = new Set()
window.run_preview_bound = false

window.resolution_presets = {
    "360p": { width: 640, height: 360 },
    "480p": { width: 854, height: 480 },
    "540p": { width: 960, height: 540 },
    "720p": { width: 1280, height: 720 },
    "1080p": { width: 1920, height: 1080 },
}

const RUN_CVARS = [
    "r_ext_compress_textures",
    "r_DynamicGlow",
    "r_vbo",
    "r_vbo_models",
    "r_surfaceSprites",
    "cg_drawFPS",
    "r_flares"
]

const STEP_SKIPPED  = -1
const STEP_WAITING  = 0
const STEP_DONE     = 1
const STEP_FAILED   = 2
const STEP_RUNNING  = 3

const q3colors = {
    '0': '#000000',
    '1': '#ff0000',
    '2': '#00ff00',
    '3': '#ffff00',
    '4': '#0000ff',
    '5': '#00ffff',
    '6': '#ff00ff',
    '7': '#ffffff',
    '8': '#ff8000',
    '9': '#808080',
}

function get_window_config()
{
    return config = window.APP_CONFIG || {}
}
function set_window_config(config)
{
    window.APP_CONFIG = config || {}
    console.log(window.APP_CONFIG);
}

function escape_html(text)
{
    return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
}

function id3_color_to_html(text)
{
    let color = q3colors['7']
    let out = `<span style="color:${color}">`

    for (let i = 0; i < text.length; i++)
    {
        if (text[i] === '^' && q3colors[text[i + 1]])
        {
            color = q3colors[text[i + 1]]
            out += `</span><span style="color:${color}">`
            i++
            continue
        }

        out += escape_html(text[i])
    }

    out += '</span>'
    return out
}

function id3_strop_color_to_html(text)
{
    return text.replace(/\^[0-9]/g, '')
}
