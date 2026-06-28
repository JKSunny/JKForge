let configOpen = false
let last_selectedRunEnvironmentId = null
let last_selectedRunId = null

async function open_config()
{
    last_selectedRunEnvironmentId = selectedRunEnvironmentId
    last_selectedRunId = selectedRunId

    close_run()

    const result = await api_get(
        "/get_config",
        "get_config"
    )

    if (!result.success)
        return

    configOpen = true

    render_config(result.config)
}

function close_config()
{
    configOpen = false

    if (last_selectedRunEnvironmentId && last_selectedRunId) {
        select_run(
            last_selectedRunEnvironmentId,
            last_selectedRunId
        )
    }
    else {
        render_no_run()
    }
}

async function fetch_config(key, value)
{
    result = await api_post(
        "/fetch_config",
        {},
        `fetch_config_${key}`
    )

    if (!result.success)
        return

    render_config(result.config)

    return result;
}

async function update_config(key, value)
{
    return await api_post(
        "/update_config",
        {
            key,
            value
        },
        `update_config_${key}`
    )
}

async function config_base_add() 
{
    return await api_post(
        "/confg_base_add",
        {},
        "config_base_add"
    )
}

async function config_base_remove(index) 
{
    return await api_post(
        "/confg_base_remove",
        {
            index
        },
        `config_base_remove_${index}`
    )
}

async function config_base_update(index, key, value) 
{
    return await api_post(
        "/confg_base_update",
        {
            index,
            key,
            value
        },
        `config_base_update_${index}_${key}`
    )
}
function render_config(config)
{
    const details = document.querySelector("#run_details")

    details.innerHTML = `
        <div class="config-page">
            <div class="config-header">
                <div>
                    <div class="config-title">
                        Global Settings
                    </div>

                    <div class="config-subtitle">
                        Configure default paths and runtime behavior
                    </div>
                </div>

                <div class="config-header-actions">
                    <button class="config-theme-toggle" onclick="cycle_theme()" title="Cycle theme">
                        <i class="fa-solid"></i>
                        <span class="config-theme-label">Theme</span>
                    </button>

                    <button onclick="close_config()">
                        <i class="fa-solid fa-arrow-left"></i>
                        Back
                    </button>
                </div>
            </div>

            <div class="config-section">
                <div class="config-toolchain config-setting">
                    ${render_config_toolchain(config)}
                </div>

                ${render_config_number_setting(
                    "HTTP Port",
                    "http_port",
                    config.http_port
                )}

                ${render_config_base_locations(
                    config.base_locations ?? []
                )}

                ${render_config_select_setting(
                    "Default run preset",
                    "default_run_preset",
                    config.default_run_preset,
                    config.run_presets ?? [],
                    "What preset to select when setting  up a new run"
                )}

                ${render_config_boolean_setting(
                    "QConsole Colors",
                    "qconsole_colors",
                    config.qconsole_colors,
                    "Enable ANSI terminal colors in qconsole output"
                )}

                ${render_config_boolean_setting(
                    "Strip Q3 Color Codes",
                    "qconsole_strip_colors",
                    config.qconsole_strip_colors,
                    "Remove ^1 style Quake color codes from output"
                )}
            </div>
        </div>
    `

    update_theme_button();
}

// toolchain
function render_config_toolchain(config)
{
    const toolchain = config.toolchain ?? []
    const generators = toolchain.generators ?? []

    return `
        <div class="config-toolchain-card">
            <div class="config-toolchain-header">
                <div class="config-setting-title">
                    Toolchain
                </div>

                <div class="config-setting-description">
                    Build tools and available generators
                </div>
            </div>

            <div class="config-toolchain-tools">
                ${render_tool_status(
                    "CMake",
                    toolchain.cmake
                )}

                ${render_tool_status(
                    "Git",
                    toolchain.git
                )}
            </div>

            <div class="config-toolchain-generators">
                <div class="config-toolchain-subtitle">
                    Generators
                </div>

                ${generators.map((generator, index) => `
                    <div class="config-generator-row">
                        <div class="config-generator-info">
                            <div class="config-generator-name">
                                ${generator.name}
                            </div>

                            <div class="config-generator-id">
                                ${generator.id}
                            </div>

                            ${config.default_generator === generator.id
                                ? `<span class="environment-badge">Default</span>`
                                : ""
                            }
                        </div>

                        <div class="config-generator-actions">
                            ${generator.valid
                                ? `<span class="config-tool-valid">
                                        <i class="fa-solid fa-check"></i>
                                   </span>`
                                : `<span class="config-tool-invalid">
                                        <i class="fa-solid fa-xmark"></i>
                                   </span>`
                            }

                            ${
                                generator.valid && config.default_generator !== generator.id
                                ? `
                                    <button onclick="handle_config_input_change(
                                                'default_generator',
                                                '${generator.id}'
                                            )
                                        "
                                    >
                                        Default
                                    </button>
                                ` 
                                : ""
                            }

                        </div>
                    </div>
                `).join("")}
            </div>
        </div>
    `
}

function render_tool_status(name, valid)
{
    return `
        <div class="config-tool-status">
            <span>${name}</span>

            ${
                valid
                ? `
                    <span class="config-tool-valid">
                        <i class="fa-solid fa-check"></i>
                        Available
                    </span>
                `
                : `
                    <span class="config-tool-invalid">
                        <i class="fa-solid fa-xmark"></i>
                        Missing
                    </span>
                `
            }
        </div>
    `
}

// base location
async function handle_config_base_add() {
    const result = await config_base_add()

    if (!result.success)
        return

    render_config(result.config)
}

async function handle_config_base_remove(index) {
    const result = await config_base_remove(index)

    if (!result.success)
        return

    render_config(result.config)
}

async function handle_config_base_update(index, key, value) {
    const result = await config_base_update(
        index,
        key,
        value
    )

    if (!result.success)
        return

    render_config(result.config)
}

function render_config_base_locations(locations) {
    return `
        <div class="config-setting config-setting-group">
            <div class="config-group-header">

                <div>
                    <div class="config-setting-title">
                        Base Locations
                    </div>

                    <div class="config-setting-description">
                        Environment root folders
                    </div>
                </div>

                <button
                    onclick="handle_config_base_add()"
                >
                    <i class="fa-solid fa-plus"></i>
                    Add
                </button>
            </div>

            ${locations.map((location, index) => `
                <div class="config-base-location">
                    <div class="config-base-header">
                        <input
                            type="text"
                            value="${location.id || ""}"
                            placeholder="Base name"
                            onchange="
                                handle_config_base_update(
                                    ${index},
                                    'id',
                                    this.value
                                )
                            "
                        />

                        <button
                            class="danger"
                            onclick="
                                handle_config_base_remove(
                                    ${index}
                                )
                            "
                        >
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>

                    <div class="config-setting-input-row">
                        <input
                            type="text"
                            value="${location.path || ""}"
                            placeholder="Path"
                            onchange="
                                handle_config_base_update(
                                    ${index},
                                    'path',
                                    this.value
                                )
                            "
                        />

                        <div class="
                            config-setting-status
                            ${location.valid?.state ? "valid" : "invalid"}
                        ">
                            <i class="fa-solid ${location.valid?.state
                                ? "fa-check"
                                : "fa-triangle-exclamation"
                            }"></i>
                        </div>

                    </div>

                    <div class="${location.valid?.state ? "config-setting-valid-path" : "config-setting-fallback"}">
                        ${location.valid?.state
                            ? "Using:"
                            : "Fallback:"}
                        <span>${location.use}</span>
                        ${location.valid.missing?.length
                                ? 
                                    `
                                        Missing: ${location.valid.missing.join(", ")} 
                                        <button class="small run" onclick="fetch_config()">
                                            <i class="fa-solid fa-arrows-rotate"></i> 
                                            Update
                                        </button>
                                    `
                                : ""}
                    </div>

                </div>
            `).join("")}
        </div>
    `
}

// global
function render_config_boolean_setting(title, key, value, description = "")
{
    return `
        <div class="config-setting">
            <div class="config-setting-info">
                <div class="config-setting-title">${title}</div>

                ${
                    description
                    ? `
                        <div class="config-setting-description">
                            ${description}
                        </div>
                    `
                    : ""
                }

            </div>

            <label class="config-toggle">
                <input type="checkbox" ${value ? "checked" : ""} onchange="handle_config_input_change('${key}',this.checked)"/>

                <span class="config-toggle-slider"></span>
            </label>
        </div>
    `
}

function render_config_path_setting(title, key, setting)
{
    const valid = setting.valid

    return `
        <div class="config-setting">
            <div class="config-setting-info">
                <div class="config-setting-title">
                    ${title}
                </div>

                <div class="config-setting-description">
                    Base directory used for environments and runs
                </div>
            </div>

            <div class="config-setting-input-wrapper">
                <div class="config-setting-input-row">
                    <input
                        type="text"
                        value="${setting.set || ""}"
                        onchange="handle_config_input_change(
                            '${key}',
                            this.value
                        )"
                    />

                    <div class="
                        config-setting-status
                        ${valid ? "valid" : "invalid"}
                    ">
                        <i class="fa-solid ${
                            valid
                            ? "fa-check"
                            : "fa-triangle-exclamation"
                        }"></i>
                    </div>
                </div>

                ${
                    valid
                    ? `
                        <div class="config-setting-valid-path">
                            Using:
                            <span>${setting.use}</span>
                        </div>
                    `
                    : `
                        <div class="config-setting-fallback">
                            Invalid path, using fallback:
                            <span>${setting.use}</span>
                        </div>
                    `
                }

            </div>
        </div>
    `
}

function render_config_number_setting(title, key, value)
{
    return `
        <div class="config-setting">
            <div class="config-setting-info">
                <div class="config-setting-title">
                    ${title}
                </div>

                <div class="config-setting-description">
                    Webserver listen port
                </div>
            </div>

            <div class="config-setting-input-wrapper">
                <input
                    type="number"
                    value="${value}"
                    onchange="handle_config_input_change(
                        '${key}',
                        parseInt(this.value)
                    )"
                />

            </div>
        </div>
    `
}

function render_config_string_setting( title, key, value, description = "")
{
    return `
        <div class="config-setting">
            <div class="config-setting-info">
                <div class="config-setting-title">
                    ${title}
                </div>

                ${
                    description
                    ? `
                        <div class="config-setting-description">
                            ${description}
                        </div>
                    `
                    : ""
                }

            </div>

            <div class="config-setting-input-wrapper">
                <input
                    type="text"
                    value="${value || ""}"
                    onchange="handle_config_input_change(
                        '${key}',
                        this.value
                    )"
                />

            </div>
        </div>
    `
}

function render_config_select_setting( title, key, value, options = [], description = "")
{
    return `
        <div class="config-setting">
            <div class="config-setting-info">
                <div class="config-setting-title">
                    ${title}
                </div>

                ${
                    description
                    ? `
                        <div class="config-setting-description">
                            ${description}
                        </div>
                    `
                    : ""
                }

            </div>

            <div class="config-setting-input-wrapper">
                <select
                    onchange="handle_config_input_change(
                        '${key}',
                        this.value
                    )"
                >

                    ${options.map(option => `
                        <option
                            value="${option}"
                            ${option === value ? "selected" : ""}
                        >
                            ${option}
                        </option>
                    `).join("")}

                </select>
            </div>
        </div>
    `
}

async function handle_config_input_change(key, value)
{
    const result = await update_config(
        key,
        value
    )

    if (!result.success)
        return

    render_config(result.config)
}