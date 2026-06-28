let selectedEnvironmentId = null

async function openEnvironmentDetaisModal(envId) 
{
    const env = current_environments.find(e => e.id === envId)

    if (!env) {
        selectedEnvironmentId = null;
        return
    }

    selectedEnvironmentId = envId;
    socket_join_env_detail( envId )

    render_environment_modal_layout()
    await init_env_console_history();

    document.getElementById("environmentDetailsModal").classList.remove("hidden")
}

function closeEnvironmentDetaisModal() 
{
    socket_leave_env_detail( selectedEnvironmentId )
    clear_env_console()
    
    selectedEnvironmentId = null

    document.getElementById("environmentDetailsModal").classList.add("hidden")
}

function render_selected_environment_modal() 
{
    if (!selectedEnvironmentId)
        return

    const env = current_environments.find(e => e.id === selectedEnvironmentId)

    if (!env)
        return

    environment_modal_update_live()
    render_env_console()
}

function render_steps(steps) 
{
    let html = '<div class="env-pipeline">'

    for (const [groupName, group] of Object.entries(steps)) {
        html += `<div class="env-pipeline-group">`

        for (const [sectionName, section] of Object.entries(group)) {
            html += `<div class="env-pipeline-section">`

            for (const [stepName, step] of Object.entries(section)) {
                const duration = format_duration( step_duration(step) )

                html += `
                    <div class="pipeline-step status-${step.status}">
                        <span class="pipeline-icon">${step_icon(step.status)}</span>
                        <span>${stepName}</span>
                        <span class="env-pipeline-duration">${duration}</span>
                    </div>
                `
            }

            html += `</div>`
        }

        html += `</div>`
    }
    html += `</div>`

    return html
}

function render_actions(env) 
{
    let html = ""

    if (git_running(env)) {
        html += `
            <button class="git" disabled>
                <i class="fa-solid fa-spinner fa-spin"></i>
                Cloning
            </button>
        `
    }

    else if (!git_finished(env)) {
        html += `
            <button class="git" onclick="trigger_git('${env.id}')">
                <i class="fa-brands fa-git-alt"></i>
                Git Clone
            </button>
        `
    }

    else if (build_running(env)) {
        html += `
            <button class="build" disabled>
                <i class="fa-solid fa-spinner fa-spin"></i>
                Building
            </button>
        `
    }

    else if (!build_finished(env)) {
        if (!git_patched(env))
        {
            html += `
                <button class="git" onclick="trigger_git_repatch('${env.id}')">
                    <i class="fa-solid fa-hammer"></i>
                    Repatch
                </b>
            `
        }
        else{
            html += `
                <button class="build" onclick="trigger_build('${env.id}')">
                    <i class="fa-solid fa-hammer"></i>
                    Build
                </button>
            `
        }
    }

    else {
        html += `
            <button class="rebuild" onclick="trigger_rebuild('${env.id}')">
                <i class="fa-solid fa-rotate-right"></i>
                Rebuild
            </button>
        `

        html += `
            <button class="run" onclick="openRunModal('${env.id}')">
                <i class="fa-solid fa-play"></i>
                Run
            </button>
        `
    }

    html += `
        <button class="red" onclick="trigger_delete('${env.id}')">
            <i class="fa-solid fa-trash"></i>
            Delete
        </button>
    `

    return html
}

function render_build_configuration(env) 
{
    const conf = env.build_configuration || {}

    return `
        ${render_badge("fa-solid fa-hammer",conf.type || "Unknown")}

        ${render_badge( "fa-solid fa-microchip", conf.arch || "Unknown" )}

        ${render_badge("fa-solid fa-gears", conf.generator?.id || "Unknown" )}

        ${conf.cmake_options
                ? `
                    <div class="env-options">
                        ${conf.cmake_options}
                    </div>
                `
                : ""
            }
    `
}

function render_client_github_configuration(env)
{
    const repo_url = `https://github.com/${env.git}`
    const commit_url = `${repo_url}/commit/${env.commit}`

    const client = get_client(env.client);
    return `
        ${render_badge( client?.frontend?.badge_icon ?? "", env.client, `client-badge ${client?.frontend?.badge_class ?? ""}` )}

        <a class="env-link" href="${repo_url}" target="_blank">
            ${render_badge( "fa-brands fa-github", env.git )}
        </a>

        ${render_badge( "fa-solid fa-code-branch", env.branch )}

        <a class="env-link" href="${commit_url}" target="_blank">
            ${render_badge( "fa-solid fa-code-commit", short_commit(env.commit) )}
        </a>
    `
}

function _environment_modal_update_pipeline( env )
{
    envDetailPipeline = document.querySelector('#environmentDetailsModelPipeline')
    envDetailPipeline.innerHTML = `
        <label>
            Pipeline
            ${render_steps(env.steps || {})}
        </label>
    `
}

function _environment_modal_update_actions( env )
{
    envDetailPipeline = document.querySelector('#environmentDetailsModelActions')
    envDetailPipeline.innerHTML = `
        ${render_actions(env)}
    `
}

function environment_modal_update_live()
{
    const env = current_environments.find(e => e.id === selectedEnvironmentId)

    if ( !env ) 
        return

    _environment_modal_update_pipeline(env)
    _environment_modal_update_actions(env)
}

function render_environment_modal_layout() 
{
    const env = current_environments.find(e => e.id === selectedEnvironmentId)

    if ( !env ) 
        return

    const content = document.querySelector(
        '#environmentDetailsModalContent'
    )

    if (!content)
        return

    content.innerHTML = `
        <div class="environment-modal-layout">
            <div class="environment-modal-header">
                <div>
                    <div class="environment-modal-title">
                        <i class="fa-solid fa-cube"></i>
                        ${env.id}
                    </div>
                </div>
                <button class="modal-close" onclick="closeEnvironmentDetaisModal()" aria-label="Close">&times;</button>
            </div>

            <div class="modal-body">
                <div class="form-row full-width">
                    <label>
                        Github Configuration
                        <div class="environment-meta">
                            ${render_client_github_configuration(env)}
                        </div>
                    </label>
                </div>

                <div class="form-row full-width">
                    <label>
                        Build Configuration
                        <div class="environment-meta">
                            ${render_build_configuration(env)}
                        </div>
                    </label>
                </div>

                <div class="form-row full-width" id="environmentDetailsModelPipeline"></div>

                <div class="run-panel">
                    <div class="panel-title">Output</div>
                    <div id="env_console" class="log-output"></div>
                </div>
            </div>

            <div class="modal-footer">
                <div class="modal-actions"id="environmentDetailsModelActions"></div>
            </div>
        </div>
    `
    /*
    // dont render these in two places.
            <div class="environment-modal-section">

                <div class="section-title">
                    Runs
                </div>

                <div class="environment-runs">
                    ${(env.runs || []).map(run => `
                        ${render_run_sidebar(env,run)}
                    `).join('')}
                </div>

            </div>
    */
}