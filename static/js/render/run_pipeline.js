function render_pipeline_step( step_id, step ) 
{
    let details_html = ""

    if (step.type === "demo_queue")
        details_html = render_demo_queue_details(step)

    let icon = "fa-circle"
    let tooltip = ""

    if (step.status === "finished")
        icon = "fa-check"

    else if (step.status === "running")
        icon = "fa-spinner fa-spin"

    else if (step.status === "failed") {
        icon = "fa-xmark"
        tooltip = `title="${escape_html(step.error || "")}"`
    }

    return `
        <div class="pipeline-step pipeline-${step.status}" ${tooltip}>
            <div class="pipeline-step-header">
                <i class="fa-solid ${icon}"></i>

                <span class="pipeline-step-name">
                    ${step_id}
                </span>

                ${
                    step.started
                    ? `
                        <span class="pipeline-step-duration">
                            ${format_run_duration(
                                run_duration({
                                    started: step.started,
                                    ended: step.ended
                                })
                            )}
                        </span>
                    `
                    : ""
                }
            </div>

            ${details_html}
        </div>
    `
}

function render_run_pipeline() 
{
    const env = current_environments.find(e => e.id === selectedRunEnvironmentId)
    const run = env?.runs?.find(r => r.id === selectedRunId)
    
    if ( !env || !run ) 
        return
    
    const pipeline = run.pipeline
    
    if ( !pipeline )
        return ""
    
    runPipeline = document.querySelector('#runPipeline')
    
    let html = ``
    const errors = []

    for (const [step_id, step] of Object.entries(pipeline.steps || {})) 
    {
        if (step.status === "failed" && step.error)
            errors.push(step.error)
    }

    for (const [step_id, step] of Object.entries(pipeline.steps || {})) 
    {
        html += render_pipeline_step(step_id, step)
    }

    html += `
        <div class="pipeline-errors">
            ${errors.map(error => `
                <div class="pipeline-error">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>${escape_html(error)}</span>
                </div>
            `).join("")}
        </div>
    `

    runPipeline.innerHTML = html
}