function openCommandModal(env_id, run_id) 
{
    activeCommandEnvId = env_id;
    activeCommandRunId = run_id;

    document.getElementById("commandInput").value = "";
    document.getElementById("commandModal").classList.remove("hidden");

    setTimeout(() => {
        document.getElementById("commandInput").focus();
    }, 50);
}

function closeCommandModal() 
{
    document.getElementById("commandModal").classList.add("hidden");
}

async function submitCommand(
    env_id = activeCommandEnvId,
    run_id = activeCommandRunId,
    command = null
) {
    if (command === null) {
        command = document.getElementById("commandInput")?.value.trim()
    }

    if (!command)
        return

    const data = await api_post(
        "/run_command",
        {
            environment: env_id,
            run: run_id,
            command
        },
        `run_command:${env_id}:${run_id}`
    )

    if (!data.success) {
        show_error(data.error || "Failed sending command")
        return
    }

    closeCommandModal()
}

document.addEventListener("keydown", (e) => 
{
    const modal = document.getElementById("commandModal");

    if (e.key === "Enter" && !modal.classList.contains("hidden")) {
        submitCommand();
    }
});