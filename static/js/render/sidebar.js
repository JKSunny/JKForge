function get_environment_expanded(env_id)
{
    return localStorage.getItem(`env-expanded:${env_id}`) !== "0"
}

function set_environment_expanded(env_id, expanded)
{
    localStorage.setItem(
        `env-expanded:${env_id}`,
        expanded ? "1" : "0"
    )
}

function get_client_group_expanded(client)
{
    return localStorage.getItem(`client-group:${client}`) !== "0"
}

function set_client_group_expanded(client, expanded)
{
    localStorage.setItem(
        `client-group:${client}`,
        expanded ? "1" : "0"
    )
}

function toggle_environment_expanded(env_id)
{
    const checkbox = document.getElementById(`env-toggle-${env_id}`)

    if (!checkbox)
        return

    set_environment_expanded(
        env_id,
        checkbox.checked
    )
}

function render_environment_sidebar(env)
{
    const expanded = get_environment_expanded(env.id)

    return `
        <input
            type="checkbox"
            class="environment-toggle"
            id="env-toggle-${env.id}"
            ${expanded ? "checked" : ""}
            onchange="toggle_environment_expanded('${env.id}')">

        <label class="environment-item" for="env-toggle-${env.id}">
            <div class="environment-item-header">

                <span class="status ${environment_status(env)}">
                    ${environment_status_icon(env)}
                </span>

                <span class="environment-name" onclick="
                    event.preventDefault();
                    openEnvironmentDetaisModal('${env.id}');
                ">
                    ${env.alias ?? env.id}
                </span>

                <i class="fa-solid fa-chevron-down environment-chevron"></i>
            </div>

            <div class="environment-meta">
                ${render_client_github_configuration(env)}
   
                ${render_build_configuration(env)}
            </div>
        </label>
    `
}

function render_run_sidebar(env, run)
{
    return `
        <button
            class="run-list-item ${selectedRunId === run.id ? 'active' : ''}"
            onclick="select_run('${env.id}','${run.id}')">

            <div class="run-list-top">
                <div class="run-title">
                    ${run_status_icon(run.status)}
                    <span>${run.alias ?? run.id}</span>
                </div>

                <span>
                    ${format_run_duration(run_duration(run))}
                </span>
            </div>

            <div class="run-list-bottom">
                ${run.launcher?.executable || '-'}
            </div>

        </button>
    `
}

function render_client_group(client, environments)
{
    if (!environments)
        return

    const expanded = get_client_group_expanded(client)
    const client_meta = get_client(client);

    return `
        <div class="client-group ${client_meta?.frontend?.badge_class ?? ""}">
            <input
                type="checkbox"
                id="client-group-${client}"
                class="client-group-toggle"
                ${expanded ? "checked" : ""}
                onchange="set_client_group_expanded(
                        '${client}',
                        this.checked
                    )
                "
            >

            <label class="client-group-header" for="client-group-${client}">
                <span>
                    <i class="${client_meta?.frontend?.badge_icon ?? ""}"></i>
                    ${client}
                </span>
                <span>${environments.length}</span>
            </label>

            <div class="client-group-content">
                ${environments.map(env => `
                    <div class="environment-group">
                        ${render_environment_sidebar(env)}

                        <div class="run-list">
                            ${(env.runs || [])
                                .map(run =>
                                    render_run_sidebar(env, run)
                                )
                                .join("")
                            }
                        </div>
                    </div>
                `).join("")}
            </div>
        </div>
    `
}

function render_environments_sidebar()
{
    const sidebar = document.querySelector('#environment_list')
    sidebar.innerHTML = ''

    if (!current_environments.length)
        return


    if (!sidebar)
        return

    const grouped = {}

    for (const env of current_environments) {
        grouped[env.client] ??= []
        grouped[env.client].push(env)
    }

    for (const [client, environments] of Object.entries(grouped)) {
        sidebar.innerHTML += render_client_group( client, environments )
    }
}
