let selectedRunEnvironmentId = null
let selectedRunId = null
let lastRunStatus = null
let runUpdateInterval = null

function render_no_run()
{
    selectedRunEnvironmentId = null
    selectedRunId = null

    const details = document.querySelector('#run_details')

    details.innerHTML = `
        <div class="empty-state">
            <i class="fa-solid fa-play"></i>
            <h2>Select a run</h2>
            <p>Choose a run from the left sidebar to inspect details.</p>
        </div>
    `
}
function run_duration(run) {
    if (!run.started) return 0
    const start = new Date(run.started)
    const end = run.ended ? new Date(run.ended) : new Date()
    return (end - start) / 1000
}

function format_run_duration(sec) {
    if (!sec) return "-"
    if (sec < 60) return `${sec.toFixed(1)}s`
    const min = Math.floor(sec / 60)
    const rem = Math.floor(sec % 60)
    return `${min}m ${rem}s`
}

function format_run_date(value) {
    if (!value) return "-"
    return new Date(value).toLocaleString()
}

function close_run()
{
    selectedRunEnvironmentId = null
    selectedRunId = null
    lastRunStatus = null

    if (runUpdateInterval) {
        clearInterval(runUpdateInterval);
        runUpdateInterval = null
    }

    document.querySelector('#run_details').innerHTML = "";

    render_no_run();
}

async function select_run(env_id, run_id) 
{
    // clear 
    socket_leave_run( selectedRunId )
    close_run();

    selectedRunEnvironmentId = env_id
    selectedRunId = run_id
    lastRunStatus = null

    // socket
    socket_join_run( run_id )

    // static
    render_run_layout()
    render_qconsole_cmd_input()
    render_run_pipeline()

    // dynamic
    await init_qconsole_history();
 
    //requestAnimationFrame(() => {
    //
    //});
    runUpdateInterval = setInterval(run_update_live, 1000)
}

function _run_update_detail_actions()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    if ( !env || !run ) 
        return

    runDetailActions = document.querySelector('#runDetailActions')

    runDetailActions.innerHTML = `
        ${run.status === 'running' ? `
            <button class="run-stop" onclick="trigger_stop_run('${env.id}','${run.id}')">
                <i class="fa-solid fa-stop"></i>
                Cancel
            </button>
        ` : ''}

        <button onclick="openRunFPSSnapshotsModal()">
            <i class="fa-solid fa-memory"></i>
            FPS Telemetry
        </button>

        <button onclick="openRunZoneSnapshotsModal()">
            <i class="fa-solid fa-memory"></i>
            Zone Memory
        </button>

        <button onclick="close_run()">
            <i class="fa-solid fa-times"></i>
            Close
        </button>
    `
}

function _run_update_status()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    if ( !env || !run ) 
        return

    runStatus = document.querySelector('#runStatus')

    const statusClass = run_status_class(run.status)

    runStatus.className = `detail-card run-status-card ${statusClass}`

    runStatus.innerHTML = `
        <span>Status</span>

        <div class="run-status-content">
            ${run_status_icon(run.status)}

            <strong>
                ${run.status || "unknown"}
            </strong>
        </div>
    `
}

function _run_update_run_duration()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    runDuration = document.querySelector('#runDuration')

    runDuration.innerHTML = `
        <span>Duration</span>
        <strong>${format_run_duration(run_duration(run))}</strong>
    `
}

function run_update_live()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    if ( !env || !run ) 
        return

    const statusChanged = lastRunStatus !== run.status
    const shouldRender = run.status === 'running' || statusChanged

    if ( !shouldRender )
        return

    lastRunStatus = run.status

    _run_update_detail_actions()
    _run_update_status()
    _run_update_run_duration()
    render_run_pipeline()
}

function render_run_layout()
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)

    if ( !env || !run ) 
        return

    const details = document.querySelector('#run_details')

    details.innerHTML = `
        <div class="details-header">
            <div>
                <div class="details-env">${env.id}</div>
                <h2>${run.id}</h2>
            </div>

            <div id="runDetailActions" class="details-actions"></div>
        </div>

        <div class="environment-meta" style="margin-bottom:2em">
            ${render_client_github_configuration(env)}

            ${render_build_configuration(env)}
        </div>

        <div class="details-grid">
            <div id="runStatus" class="detail-card"></div>

            <div class="detail-card">
                <span>Started</span>
                <strong>${format_run_date(run.started)}</strong>
            </div>

            <div id="runDuration" class="detail-card"></div>
        </div>

        <div class="run-panel">
            <div class="panel-title">Launcher</div>
            <div class="launcher-path">Executable: ${run.launcher?.executable || '-'}</div>
            <div class="launcher-path">Base path: ${run.launcher?.base_dir || '-'}</div>
            <div class="launcher-args log-output">${(run.launcher?.arguments || []).join(' ')}</div>
        </div>

        <div class="run-panel">
            <div class="panel-title">Pipeline</div>
            <div class="panel-title"></div>
            <div id="runPipeline" class="run-pipeline"></div>
        </div>

        <div class="run-panel">
            <div class="panel-title">Console</div>
            <div id="qconsole" class="log-output"></div>
            <div id="qconsole_cmd"></div>
        </div>
    `
}