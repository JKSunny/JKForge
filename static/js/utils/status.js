function step_running(step) 
{
    return step?.status === STEP_RUNNING
}

function step_finished(step) 
{
    return [STEP_SKIPPED, STEP_DONE, STEP_FAILED].includes(step?.status)
}

function step_failed(step) 
{
    return [STEP_FAILED].includes(step?.status)
}

function step_duration(step) 
{
    const done_states = [
        STEP_SKIPPED, 
        STEP_DONE, 
        STEP_FAILED
    ]

    if (done_states.includes(step.status))
        return step.duration || 0

    if (step.status === STEP_RUNNING && step.started) {
        const started = new Date(step.started)
        const now = new Date()

        return (now - started) / 1000
    }

    return 0
}

function git_running(env) 
{
    const setup = env?.steps?.environment?.setup || {}

    return (
        step_running(setup.git_fetch) ||
        step_running(setup.git_patch) ||
        step_running(setup.checkout_commit)
    )
}

function build_running(env) 
{
    const build = env?.steps?.environment?.build || {}

    return (
        step_running(build.cmake_configure) ||
        step_running(build.cmake_build) ||
        step_running(build.cmake_install)
    )
}

function git_finished(env) 
{
    const setup = env?.steps?.environment?.setup || {}

    return (
        step_finished(setup.git_fetch) &&
        step_finished(setup.git_patch) &&
        step_finished(setup.checkout_commit)
    )
}

function git_patched(env) 
{
    const setup = env?.steps?.environment?.setup || {}

    return (
        !step_failed(setup.git_patch)
    )
}

function build_finished(env) 
{
    const build = env?.steps?.environment?.build || {}

    return (
        step_finished(build.cmake_configure) &&
        step_finished(build.cmake_build) &&
        step_finished(build.cmake_install)
    )
}

function environment_status_icon(env) 
{

    const status = environment_status(env)

    switch (status) {
        case "running":
            return `<i class="fa-solid fa-spinner fa-spin"></i>`
        case "success":
            return `<i class="fa-solid fa-check"></i>`
        default:
            return `<i class="fa-regular fa-circle"></i>`
    }
}
function environment_status(env) 
{

    if (git_running(env) || build_running(env))
        return "running"

    if (git_finished(env) && build_finished(env))
        return "success"

    return "idle"
}

function step_icon(status) 
{
    switch (status) {
        case STEP_SKIPPED:  return `<i class="fa-solid fa-minus"></i>`
        case STEP_WAITING:  return `<i class="fa-regular fa-clock"></i>`
        case STEP_DONE:     return `<i class="fa-solid fa-check"></i>`
        case STEP_FAILED:   return `<i class="fa-solid fa-xmark"></i>`
        case STEP_RUNNING:  return `<i class="fa-solid fa-spinner fa-spin"></i>`
    }

    return `<i class="fa-solid fa-circle"></i>`
}

function run_status_class(status)
{
    switch (status)
    {
        case "running":     return "status-running"
        case "success":
        case "finished":    return "status-success"
        case "failed":      return "status-failed"
        default:            return "status-unknown"
    }
}

function run_status_icon(status) 
{
    const status_class = run_status_class(status)

    let html = ``

    switch (status) {
        case "running":
            html += `<i class="fa-solid fa-spinner fa-spin"></i>`
            break;
        case "success":
        case "finished":
            html += `<i class="fa-solid fa-check"></i>`
            break;
        case "failed":
            html += `<i class="fa-solid fa-xmark"></i>`
            break;
        default:
            html += `<i class="fa-regular fa-circle"></i>`
            break;
    }
    
    return `
        <span class="status-icon ${status_class}">
            ${html}
        </span>
    `
}