let qconsoleOutput = {}
function qconsole_key(env_id, run_id) {
    return `${env_id}:${run_id}`
}

function render_qconsole_cmd_input()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    if ( !env || !run ) 
        return

    qconsole_cmd = document.querySelector('#qconsole_cmd')
    const qconsoleInputValue = document.getElementById("qconsoleInput")?.value || ""

    qconsole_cmd.innerHTML = (run.status === "running")
        ? `
            <div class="qconsole-input-row">
                <input
                    id="qconsoleInput"
                    value="${qconsoleInputValue}"
                    type="text"
                    placeholder="Enter console command..."
                    onkeydown="
                        if(event.key === 'Enter')
                            submit_qconsole_command()
                    "
                />

                <button class="blue" onclick="submit_qconsole_command()" >
                    <i class="fa-solid fa-paper-plane"></i>
                    Send
                </button>
            </div>
        `
        : ""
}

function render_qconsole()
{
    const qconsole = document.querySelector('#qconsole')

    if (!qconsole)
        return

    const config = get_window_config()

    const key = qconsole_key(selectedRunEnvironmentId, selectedRunId)
    const text = qconsoleOutput[key] || ""

    if (config.qconsole_colors)
        qconsole.innerHTML = id3_color_to_html(text)

    else if (config.qconsole_strip_colors)
        qconsole.textContent = id3_strop_color_to_html(text)

    else
        qconsole.textContent = text

    qconsole.scrollTop = qconsole.scrollHeight
}

async function init_qconsole_history() {
    const data = await api_post(
        "/get_qconsole",
        {
            environment: selectedRunEnvironmentId,
            run: selectedRunId,
        },
        `get_qconsole:${selectedRunEnvironmentId}${selectedRunId}:`
    )

    if (!data.success)
        return

    const key = qconsole_key(selectedRunEnvironmentId, selectedRunId)
    qconsoleOutput[key] = data.content

    render_qconsole()
}

function append_qconsole( data )
{
    const key = qconsole_key(data.environment,  data.run)

    if (!qconsoleOutput[key])
        qconsoleOutput[key] = ""

    qconsoleOutput[key] += data.append

    if ( data.environment === selectedRunEnvironmentId && data.run === selectedRunId ) {
        render_qconsole()
    }
}

async function submit_qconsole_command() 
{
    const input = document.getElementById("qconsoleInput")

    if (!input)
        return

    const command = input.value.trim()

    if (!command)
        return

    await submitCommand(
        selectedRunEnvironmentId,
        selectedRunId,
        command
    )

    input.value = ""
}