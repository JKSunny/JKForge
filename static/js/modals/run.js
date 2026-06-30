function setSelectOption(id, value) 
{
    console.log(id)
    console.log(id)
    const select = document.getElementById(id)

    if (value === undefined) 
        return

    const exists = [...select.options].some(opt => opt.value === value)
    select.value = exists ? value : select.options[0]?.value
}

function collectRunPresetData() 
{
    const cvars = {}

    for (const cvar of RUN_CVARS) {
        const el = document.getElementById(`cvar_${cvar}`)

        if (el)
            cvars[cvar] = el.checked
    }

    return {
        executable:         document.getElementById("runExecutable").value,
        base_id:            parseInt(document.getElementById("baseLocation").value),
        renderer:           document.getElementById("runRenderer").value,
        fs_game:            document.getElementById("runFsGame").value.trim(),
        custom:             document.getElementById("runCustomArgs").value.trim(),
        developer:          document.getElementById("runDeveloper").checked,
        windowed:           document.getElementById("runWindowed").checked,
        resolution:         document.getElementById("runResolution").value,
        pipeline_preset:    document.getElementById("runPipelinePreset").value,
        cvars
    }
}

async function saveRunPreset(save_as = false) 
{
    let preset_id = document.getElementById("runPreset").value

    if (save_as || !preset_id) {

        preset_id = prompt(
            "Preset name"
        )?.trim()

        if (!preset_id)
            return
    }

    const preset = collectRunPresetData()

    const data = await api_post(
        "/save_run_preset",
        {
            preset_id,
            preset
        },
        `save_run_preset:${preset_id}`
    )

    if (!data.success) {
        alert(data.error || "Failed saving preset")
        return
    }

    window.runPresets[preset_id] = preset

    const select =
        document.getElementById("runPreset")

    if (![...select.options].find(x => x.value === preset_id)) {

        select.innerHTML += `
            <option value="${preset_id}">
                ${preset_id}
            </option>
        `
    }

    select.value = preset_id
}

function renderPipelinePreviewStepDetails(step)
{
    let details = "";

    if (step.type === "demo_queue") {
        const demos = step.input?.demos ?? "all"

        details = `
            <div class="pipeline-preview-info">
                <i class="fa-solid fa-list"></i>

                <div class="pipeline-preview-popup">
                    ${
                        demos === "all"
                            ? `<span class="pipeline-tag">All demos</span>`
                            : demos.map(demo => `
                                <div class="pipeline-demo">
                                    <i class="fa-solid fa-clapperboard"></i>
                                    <span>${demo}</span>
                                </div>
                            `).join("")
                    }
                </div>
            </div>
        `;
    }

    return details
}

function renderPipelinePreview() 
{
    const preset_id = document.getElementById("runPipelinePreset").value
    const preset    = window.pipelinePresets?.[preset_id]
    const container = document.getElementById("runPipelinePreview")

    if (!preset) {
        container.innerHTML = ""
        return
    }

    const steps = preset.steps.map((step, index) => `
        <div class="pipeline-preview-step">
            <span class="pipeline-preview-step-id">
                ${step.id}
            </span>

            <span class="pipeline-preview-step-type">
                ${step.type}
            </span>

            ${renderPipelinePreviewStepDetails(step)}
        </div>

        ${index < preset.steps.length - 1 ? `
            <div class="pipeline-preview-connector">
                <i class="fa-solid fa-chevron-right"></i>
            </div>
        ` : ""}
    `).join("")

    container.innerHTML = `
        <div class="pipeline-preview-header">
            <div class="pipeline-preview-title">
                <i class="fa-solid fa-diagram-project"></i>
                ${preset.name}
            </div>

            <div class="pipeline-preview-description">
                ${preset.description || "No description"}
            </div>
        </div>

        <div class="pipeline-preview-steps">
            ${steps}
        </div>
    `
}

function renderCvarCheckboxes() 
{
    return RUN_CVARS.map(cvar => `
        <label class="setting-row">
            <span class="setting-label">
                ${cvar}
            </span>

            <span class="config-toggle">
                <input
                    id="cvar_${cvar}"
                    type="checkbox">

                <span class="config-toggle-slider">
                </span>
            </span>
        </label>
    `).join("")
}

function setCvarCheckboxes(cvars = {}) 
{
    for (const cvar of RUN_CVARS) {
        const el = document.getElementById(`cvar_${cvar}`)

        if (!el)
            continue

        el.checked = !!cvars[cvar]
    }
}

function getCvarArguments() 
{
    const args = []

    for (const cvar of RUN_CVARS) {
        const el = document.getElementById(`cvar_${cvar}`)

        if (!el)
            continue

        args.push(
            "+set",
            cvar,
            el.checked ? "1" : "0"
        )
    }

    return args
}

function selectRendererByPreset(preset) 
{
    if (!preset.renderer_contains)
        return

    const renderer = document.getElementById("runRenderer")
    const wanted = normalizeRendererName(preset.renderer_contains)

    for (const option of renderer.options) {

        const value =
            normalizeRendererName(option.value)

        if (value.includes(wanted)) {
            renderer.value = option.value
            return
        }
    }
}
function selectPipelineByPreset(preset) 
{
    if (!preset.pipeline_preset)
        return

    const pipeline = document.getElementById("runPipelinePreset")

    for (const option of pipeline.options) {

        const value = option.value

        if (option.value === preset.pipeline_preset) {
            pipeline.value = option.value
            return
        }
    }
}

function applyRunPreset() 
{
    const preset_id = document.getElementById("runPreset").value

    const preset = window.runPresets[preset_id]

    if (!preset)
        return

    console.log(preset)
    setSelectOption("runExecutable", preset.executable)
    setSelectOption("runRenderer", preset.renderer)
    setSelectOption("runResolution", preset.resolution)
    setSelectOption("baseLocation", preset.base_id.toString())

    if (preset.fs_game !== undefined)
        document.getElementById("runFsGame").value = preset.fs_game

    if (preset.custom !== undefined)
        document.getElementById("runCustomArgs").value = preset.custom

    if (preset.developer !== undefined)
        document.getElementById("runDeveloper").checked = preset.developer

    if (preset.windowed !== undefined)
        document.getElementById("runWindowed").checked = preset.windowed

    selectRendererByPreset(preset)
    selectPipelineByPreset(preset)
    renderPipelinePreview();

    if (preset.cvars)
        setCvarCheckboxes(preset.cvars)

    updateRunPreview()
}

async function openRunModal(env_id) 
{
    current_run_environment = env_id
    const config = get_window_config()

    const data = await api_post(
        "/get_run_presets",
        {
            environment: env_id
        },
        `get_run_presets:${env_id}`
    )

    if (!data.success)
        return

    window.runPresets       = data.presets || {}
    window.pipelinePresets  = data.pipeline_presets || {}

    // run presets
    const presetSelect = document.getElementById("runPreset")
    presetSelect.innerHTML = Object.keys(window.runPresets)
        .map(x => `
            <option value="${x}">
                ${x}
            </option>
        `)
        .join("")

    // select default
    if (window.runPresets?.[data.defaults?.run_preset])
        presetSelect.value = data.defaults?.run_preset

    // pipeline presets
    const pipelineSelect = document.getElementById("runPipelinePreset")
    pipelineSelect.innerHTML =
        Object.entries(window.pipelinePresets)
            .map(([id, preset]) => `
                <option value="${id}">
                    ${preset.name}
                </option>
            `)
            .join("")

    document.getElementById("runEnvironment").value = env_id

    const executable = document.getElementById("runExecutable")
    const renderer = document.getElementById("runRenderer")
    const resolution = document.getElementById("runResolution")
    const base_location = document.getElementById("baseLocation")

    executable.innerHTML = data.executables
        .map(x => `<option value="${x}">${x}</option>`)
        .join("")

    renderer.innerHTML = data.renderers
        .map(x => `<option value="${x}">${x}</option>`)
        .join("")

    resolution.innerHTML =
        `<option value="">Default</option>` +
        Object.entries(window.resolution_presets)
            .map(([key, value]) => `
                <option value="${key}">
                    ${value.width}x${value.height}
                </option>
            `)
        .join("")

    base_locations = config.base_locations ?? []
    base_location.innerHTML = base_locations
        .map((location, index) => `<option value="${index}">${location.id}</option>`)
        .join("")

    document.getElementById("cvarGrid").innerHTML = renderCvarCheckboxes();

    applyRunPreset()

    updateRunPreview()

    bindRunPreviewUpdates();
    document.getElementById("runModal").classList.remove("hidden")
}

function closeRunModal() 
{
    document.getElementById("runModal").classList.add("hidden")
}

function collectRunConfig() 
{
    const executable        = document.getElementById("runExecutable").value
    const renderer          = document.getElementById("runRenderer").value
    const fs_game           = document.getElementById("runFsGame").value.trim()
    const custom            = document.getElementById("runCustomArgs").value.trim()
    const developer         = document.getElementById("runDeveloper").checked
    const windowed          = document.getElementById("runWindowed").checked
    const pipeline_preset   = document.getElementById("runPipelinePreset").value
    const base_location     = parseInt(document.getElementById("baseLocation").value)

    const resolution    = window.resolution_presets[
        document.getElementById("runResolution").value
    ]

    const args = []

    if (renderer)
        args.push("+set", "cl_renderer", renderer)

    if (developer)
        args.push("+set", "developer", "1")

    if (windowed)
        args.push("+set", "r_fullscreen", "0")

    if (resolution) {
        args.push("+set", "r_customwidth", String(resolution.width))
        args.push("+set", "r_customheight", String(resolution.height))
        args.push("+set", "r_mode", "-1")
    }

    if (fs_game)
        args.push("+set", "fs_game", fs_game)

    args.push(...getCvarArguments())

    if (custom)
        args.push(...splitArguments(custom))

    return {
        executable,
        arguments: args,
        base_id: base_location,
        pipeline_preset: pipeline_preset,
    }
}

function buildRunCommand() 
{
    const launcher = collectRunConfig()

    return `${launcher.executable} ${launcher.arguments.join(" ")}`
}

function bindRunPreviewUpdates() 
{
    if (run_preview_bound)
        return

    run_preview_bound = true

    const ids = [
        "runExecutable",
        "runRenderer",
        "runFsGame",
        "runCustomArgs",
        "runDeveloper",
        "runWindowed",
        "runResolution",
        ...RUN_CVARS.map(x => `cvar_${x}`)
    ]

    for (const id of ids) {
        const el = document.getElementById(id)

        el?.addEventListener("input", updateRunPreview)
        el?.addEventListener("change", updateRunPreview)
    }
}

document.addEventListener("change", e => 
    {
    if (e.target.id === "runPreset")
        applyRunPreset()

    if (e.target.id === "runPipelinePreset")
        renderPipelinePreview()
})

function updateRunPreview() 
{
    document.getElementById("runCommandPreview").textContent = buildRunCommand()
}

async function setDefaultEnvPreset()
{
    const preset_id = document.getElementById("runPreset").value
    const preset = window.runPresets[preset_id]

    if (!preset)
        return

    const data = await api_post(
        "/set_default_run_preset",
        {
            environment: current_run_environment,
            preset_id: preset_id
        },
        `set_default_run_preset:${current_run_environment}`
    )
}

async function submitRun() 
{
    if (!current_run_environment)
        return

    const launcher = collectRunConfig()

    const data = await api_post(
        "/run",
        {
            environment: current_run_environment,
            launcher
        },
        `run:${current_run_environment}`
    )

    if (data.success) {
        console.log("Run result:", data)
        closeEnvironmentDetaisModal()
        closeRunModal()
    }
}