function openEnvironmentAddModal() 
{
    const config = get_window_config()
    const clients = document.getElementById("environmentClient")
    const generator = document.getElementById("environmentGenerator")

    clients.innerHTML = config.clients_meta
        .map(x => `<option value="${x.name}">${x.name}</option>`)
        .join("")

    generator.innerHTML = (config.toolchain?.generators ?? [])
        .map(generator => { return generator.valid ? `<option value="${generator.id}">${generator.name}</option>` : ""})
        .join("")

    if (config.toolchain?.generators?.some( g => g.id === config.default_generator && g.valid )) {
        generator.value = config.default_generator
    }
    
    document.getElementById("environmentAddModal").classList.remove("hidden");
}

function closeEnvironmentAddModal() 
{
    document.getElementById("environmentAddModal").classList.add("hidden");
}

function toggleAdvancedEnvironment() 
{
    document.getElementById("environmentAdvanced").classList.toggle("hidden")
}

function find_generator( generator_id )
{
    const config = get_window_config()
    return config?.toolchain?.generators?.find(g => g.id === generator_id)
}

async function create_environment() 
{
    const type          = document.getElementById("environmentType").value
    const git           = document.getElementById("environmentGit").value.trim()
    const branch        = document.getElementById("environmentBranch").value.trim()
    const commitRaw     = document.getElementById("environmentCommit").value.trim()
    const commit        = commitRaw.length ? commitRaw : null
    const arch          = document.getElementById("environmentArch").value
    const generator     = find_generator(document.getElementById("environmentGenerator").value)
    const cmake_options = document.getElementById("environmentCMakeOptions").value.trim()

    const client        = document.getElementById("environmentClient").value.trim()

    const data = await api_post(
        "/environment_add",
        {
            type,
            client,
            git,
            branch,
            commit,
            arch,
            generator,
            cmake_options
        },
        "environment_add"
    )

    if (data.success) {
        closeEnvironmentAddModal()
    }
}