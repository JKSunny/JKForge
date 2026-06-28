function get_demo_status_icon_meta(status) {
    switch (status) {
        case "finished":
            return {
                icon: "fa-check",
                className: "demo-finished"
            }

        case "running":
            return {
                icon: "fa-play",
                className: "demo-running"
            }

        case "loading":
            return {
                icon: "fa-spinner fa-spin",
                className: "demo-loading"
            }

        case "failed":
            return {
                icon: "fa-xmark",
                className: "demo-failed"
            }

        default:
            return {
                icon: "fa-circle",
                className: "demo-pending"
            }
    }
}

function render_demo_queue_details(step) {
    const details = step.details

    if (!details)
        return ""

    const repeatDisplay = details.repeat > 0 ? details.repeat : `<i class="fa-solid fa-infinity"></i>`

    let html = `
        <div class="demo-queue-details">
            <div class="demo-queue-header">
                <div class="demo-queue-stat">
                    <span class="label">Demos</span>
                    <span class="value">
                        ${details.completed_demos}/${details.total_demos}
                    </span>
                </div>

                <div class="demo-queue-stat">
                    <span class="label">Loop</span>
                    <span class="value">
                        ${details.current_repeat+1}/${repeatDisplay}
                    </span>
                </div>

                    ${
                        details.current_demo
                        ? (() => {

                        const current = details.demos?.[details.current_demo]
                        const meta = get_demo_status_icon_meta(current?.status)

                        return `
                            <div class="demo-queue-current">
                                <i class="fa-solid ${meta.icon}"></i>
                                ${details.current_demo}
                            </div>
                        `
                    })()
                    : ""
                }

            </div>
            <div class="demo-queue-list">
    `

    for (const [demo_name, demo] of Object.entries(details.demos || {})) {
        let icon = "fa-circle"

        if (demo.status === "finished")
            icon = "fa-check"

        else if (demo.status === "running")
            icon = "fa-play"

        else if (demo.status === "loading")
            icon = "fa-spinner fa-spin"

        else if (demo.status === "failed")
            icon = "fa-xmark"

        html += `
            <div class="demo-queue-item demo-${demo.status}">
                <div class="demo-queue-item-left">
                    <i class="fa-solid ${icon}"></i>

                    <span class="demo-name">
                        ${demo_name}
                    </span>
                </div>
                <div class="demo-queue-item-right">

                    ${
                        demo.load_time
                        ? `
                            <span class="demo-load-time">
                                ${demo.load_time.toFixed(2)}s
                            </span>
                        `
                        : ""
                    }

                    <span>
                        x${demo.plays}
                    </span>

                </div>
            </div>
        `
    }

    html += `
            </div>
        </div>
    `

    return html
}
