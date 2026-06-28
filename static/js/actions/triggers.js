
async function trigger_git_repatch(env_id) {

    const data = await api_post("/git_repatch", {
        environment: env_id
    }, `git_repatch:${env_id}`)

    if (data.success)
        console.log("Git repatch result:", data)
}

async function trigger_git(env_id) {

    const data = await api_post("/git", {
        environment: env_id
    }, `git:${env_id}`)

    if (data.success)
        console.log("Git result:", data)
}

async function trigger_build(env_id) {
    const data = await api_post("/build", {
        environment: env_id
    }, `build:${env_id}`)

    if (data.success)
        console.log("Build result:", data)
}

async function trigger_rebuild(env_id) {
    const data = await api_post("/rebuild", {
        environment: env_id
    }, `rebuild:${env_id}`)

    if (data.success)
        console.log("Rebuild result:", data)
}

async function trigger_delete(env_id) {
    if (!confirm(`Delete environment '${env_id}'?`))
        return

    const data = await api_post("/delete", {
        environment: env_id
    }, `delete:${env_id}`)

    if (data.success)
        console.log("Delete result:", data)
}

async function trigger_stop_run(env_id, run_id) {
    const data = await api_post("/run_stop", {
        environment: env_id,
        run: run_id
    }, `run_stop:${env_id}:${run_id}`)

    if (data.success)
        console.log("Run stopped:", data)
}