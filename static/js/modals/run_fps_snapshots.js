let FPSSnapshots = {}

async function openRunFPSSnapshotsModal(env_id, run_id)
{
    await get_fps_snapshots();

    document.getElementById("runFPSSnapshotsModal").classList.remove("hidden");
}

function closeRunFPSSnapshotsModal() 
{
    document.getElementById("runFPSSnapshotsModal").classList.add("hidden");
}

async function get_fps_snapshots()
{
    const data = await api_post(
        "/get_fps_snapshots",
        {
            environment: selectedRunEnvironmentId,
            run: selectedRunId,
        },
        `get_fps_snapshots:${selectedRunEnvironmentId}${selectedRunId}:`
    )

    if (!data.success)
        return

    FPSSnapshots = data
    render_fps_snapshots();
}

function fps_stats(frames)
{
    if (!frames?.length)
        return null

    let min = Infinity
    let max = -Infinity
    let total = 0

    for (const fps of frames)
    {
        if (fps < min)
            min = fps

        if (fps > max)
            max = fps

        total += fps
    }

    const avg = total / frames.length

    const sorted =
        [...frames]
            .sort((a, b) => a - b)

    const p1 =
        sorted[
            Math.floor(sorted.length * 0.01)
        ] || 0

    const p01 =
        sorted[
            Math.floor(sorted.length * 0.001)
        ] || 0

    return {
        avg,
        min,
        max,
        p1,
        p01
    }
}

function render_fps_snapshots()
{
    const container = document.querySelector('#fps_telemetry')

    if (!container)
        return

    const snapshots =
        Object.values(
            FPSSnapshots?.snapshots?.snapshots || {}
        )

    if (!snapshots.length)
    {
        container.innerHTML = `
            <div class="empty-state">
                No FPS telemetry
            </div>
        `
        return
    }

    const summary = snapshots.map(snapshot => {
        const stats = fps_stats(snapshot.frames || [])

        return {
            snapshot,
            stats
        }
    })

    const labels =
        summary.map((x, i) =>
            x.snapshot.identifier || `Run ${i + 1}`
        )

    const avgData =
        summary.map(x => x.stats.avg)

    const minData =
        summary.map(x => x.stats.min)

    const p1Data =
        summary.map(x => x.stats.p1)

    const p01Data =
        summary.map(x => x.stats.p01)

    container.innerHTML = `
        <div class="fps-global-chart-wrap">
            <div id="fps_global_chart"></div>
        </div>

        <div class="fps-summary-grid">

            ${
                summary.map((x, i) => `

                    <div class="fps-card">
                        <div class="fps-card-title">
                            ${x.snapshot.identifier}
                        </div>

                        <div class="fps-main-stat">
                            ${x.stats.avg.toFixed(1)}
                            <span>avg fps</span>
                        </div>

                        <div class="fps-mini-grid">
                            <div>
                                <span>1% low</span>
                                <strong>${x.stats.p1.toFixed(1)}</strong>
                            </div>

                            <div>
                                <span>0.1% low</span>
                                <strong>${x.stats.p01.toFixed(1)}</strong>
                            </div>

                            <div>
                                <span>min</span>
                                <strong>${x.stats.min.toFixed(1)}</strong>
                            </div>

                            <div>
                                <span>max</span>
                                <strong>${x.stats.max.toFixed(1)}</strong>
                            </div>

                            <div>
                                <span>frames</span>
                                <strong>${x.snapshot.frameCount}</strong>
                            </div>
                        </div>

                        <div id="fps_chart_${i}" class="fps-inline-chart"></div>
                    </div>
                `).join("")
            }
        </div>
    `

    // inline frametime graph
    summary.forEach((x, i) => {
        const el = document.querySelector(`#fps_chart_${i}`)
        const frames = x.snapshot.frames || []
        const xs = frames.map((_, i) => i)
        const fps = frames.map(ft => ft)

        new uPlot(
            {
                width: 320,
                height: 120,

                legend: {
                    show: false
                },

                axes: [
                    { show: false },
                    { show: false }
                ],

                scales: {
                    x: { time: false }
                },

                series: [
                    {},
                    {
                        stroke: "rgb(88,166,255)",
                        fill: "rgba(88,166,255,.12)",
                        width: 2
                    }
                ]
            },
            [xs, fps],
            el
        )
    })

    // global comparison chart
    new uPlot(
        {
            title: "FPS Comparison",

            width: 1200,
            height: 420,

            scales: {
                x: { time: false }
            },

            axes: [
                { show: false },
                { show: false }
            ],

            series: [
                {},

                {
                    label: "Average FPS",
                    stroke: "rgb(88,166,255)",
                    width: 3,
                    points: {
                        show: true
                    }
                },

                {
                    label: "1% Low",
                    stroke: "rgb(242,204,96)",
                    width: 2,
                    points: {
                        show: true
                    }
                },

                {
                    label: "0.1% Low",
                    stroke: "rgb(255,123,114)",
                    width: 2,
                    points: {
                        show: true
                    }
                },

                {
                    label: "Minimum FPS",
                    stroke: "rgb(126,231,135)",
                    width: 2,
                    points: {
                        show: true
                    }
                }
            ]
        },

        [
            labels.map((_, i) => i),
            avgData,
            p1Data,
            p01Data,
            minData
        ],

        document.querySelector('#fps_global_chart')
    )
}