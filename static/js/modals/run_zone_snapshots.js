async function openRunZoneSnapshotsModal(env_id, run_id) {
    await get_zone_memory_snapshots();

    document.getElementById("runZoneSnapshotsModal").classList.remove("hidden");
}

function closeRunZoneSnapshotsModal() {
    document.getElementById("runZoneSnapshotsModal").classList.add("hidden");
}

// zone memory
let zoneRenderViewType = 1;
let zoneMemorySnapshots = {}

function tag_to_color(tag)
{
    const colors = [
        "#58a6ff",
        "#ff7b72",
        "#3fb950",
        "#d29922",
        "#bc8cff",
        "#f78166",
        "#56d4dd",
        "#e3b341",
        "#ffa657",
        "#8ddb8c",
        "#79c0ff",
        "#ff9bce",
    ]

    let hash = 0

    for (let i = 0; i < tag.length; i++)
        hash = ((hash << 5) - hash) + tag.charCodeAt(i)

    return colors[Math.abs(hash) % colors.length]
}

function set_zone_view(type)
{
    zoneRenderViewType = type
    render_zone_memory_snapshots()
}

function get_zone_snapshot_entries ()
{
    const snapshots = zoneMemorySnapshots?.snapshots?.snapshots || {}

    return Object.entries(snapshots).sort(([a], [b]) => a.localeCompare(b))
}

async function get_zone_memory_snapshots()
{
    const data = await api_post(
        "/get_zone_snapshots",
        {
            environment: selectedRunEnvironmentId,
            run: selectedRunId,
        },
        `get_zone_snapshots:${selectedRunEnvironmentId}${selectedRunId}:`
    )

    if (!data.success)
        return

    zoneMemorySnapshots = data
    render_zone_memory_snapshots();
}

function clear_zone_chart_snapshots_html()
{
    const zone_memory = document.querySelector('#zone_memory')
    const legend_el = document.querySelector('#zone_memory_legend')

    if (zone_memory)
        zone_memory.innerHTML = ""

    if (legend_el)
        legend_el.innerHTML = ""
}

function render_zone_memory_snapshots()
{
    clear_zone_chart_snapshots_html()

    switch (zoneRenderViewType)
    {
        case 1:
            return render_zone_memory_heatmap()

        case 2:
            return render_zone_memory_timeline()

        case 3:
            return render_zone_memory_stacked()

        case 4:
            return render_zone_chart()

        default:
            return render_zone_memory_heatmap()
    }
}

function render_zone_memory_heatmap()
{
    const zone_memory = document.querySelector('#zone_memory')

    if (!zone_memory)
        return

    const entries = get_zone_snapshot_entries();
   
    if (!entries.length) {
        zone_memory.innerHTML = `
            <div class="empty-state">
                No zone snapshots
            </div>
        `
        return
    }

    // gather all unique tags
    const all_tags = new Set()

    for (const [, snapshot] of entries) {
        for (const tag of snapshot.tags || [])
            all_tags.add(tag.tag)
    }

    const tags =
        [...all_tags].sort()

    // max memory for normalization
    let max_mb = 0

    for (const [, snapshot] of entries) {
        for (const tag of snapshot.tags || [])
            max_mb = Math.max(max_mb, tag.mb || 0)
    }

    zone_memory.innerHTML = `
        <div class="zone-memory-grid">

            <div class="zone-memory-header">
                <div class="zone-memory-corner">
                    Tag
                </div>

                ${
                    entries.map(([snapshot_id], index) => `
                        <div class="zone-memory-column-label">
                            ${index}
                        </div>
                    `).join("")
                }
            </div>

            ${
                tags.map(tag_name => {

                    return `
                        <div class="zone-memory-row">

                            <div class="zone-memory-tag">
                                ${tag_name}
                            </div>

                            ${
                                entries.map(([, snapshot]) => {

                                    const tag =
                                        (snapshot.tags || [])
                                            .find(x => x.tag === tag_name)

                                    const mb = tag?.mb || 0

                                    const alpha =
                                        Math.max(
                                            0.08,
                                            mb / max_mb
                                        )

                                    return `
                                        <div
                                            class="zone-memory-cell"
                                            title="
                                                ${snapshot.identifier}
                                                Total: ${snapshot.totalBytes}
                                                Peak: ${snapshot.peakBytes}
                                                Blocks: ${snapshot.totalBlocks}
                                            "
                                            style="
                                                background:
                                                    rgba(
                                                        88,
                                                        166,
                                                        255,
                                                        ${alpha}
                                                    );
                                            "
                                        >
                                            ${
                                                mb > 0
                                                ? mb.toFixed(1)
                                                : ""
                                            }
                                        </div>
                                    `
                                }).join("")
                            }

                        </div>
                    `
                }).join("")
            }

        </div>
    `

    // set css snapshot count
    zone_memory.querySelector(".zone-memory-grid")?.style.setProperty(
        "--snapshot-count",
        entries.length
    )
}

function render_zone_memory_timeline()
{
    const zone_memory =
        document.querySelector('#zone_memory')

    if (!zone_memory)
        return

    const entries = get_zone_snapshot_entries()

    zone_memory.innerHTML = `
        <div class="zone-timeline">

            ${
                entries.map(([id, snapshot], index) => `

                    <div class="zone-timeline-node">

                        <div class="zone-timeline-card">

                            <div class="zone-timeline-header">
                                ${snapshot.identifier || id}
                            </div>

                            <div class="zone-timeline-total">
                                ${(snapshot.totalBytes / 1024 / 1024).toFixed(1)} MB
                            </div>

                            <div class="zone-timeline-tags">
                                ${
                                    (snapshot.tags || [])
                                        .sort((a,b)=>b.bytes-a.bytes)
                                        .slice(0,3)
                                        .map(x => `
                                            <span>
                                                ${x.tag}
                                            </span>
                                        `)
                                        .join("")
                                }
                            </div>

                        </div>

                        ${
                            index < entries.length - 1
                            ? `
                                <div class="zone-timeline-arrow">
                                    <i class="fa-solid fa-arrow-right"></i>
                                </div>
                            `
                            : ""
                        }

                    </div>

                `).join("")
            }

        </div>
    `
}

function render_zone_memory_stacked()
{
    const zone_memory = document.querySelector('#zone_memory')

    if (!zone_memory)
        return

    const entries =
        get_zone_snapshot_entries()

    let max_total = 0

    for (const [, snapshot] of entries)
        max_total = Math.max(
            max_total,
            snapshot.totalBytes || 0
        )

    zone_memory.innerHTML = `
        <div class="zone-stacked">

            ${
                entries.map(([id, snapshot]) => {

                    const total_mb =
                        snapshot.totalBytes / 1024 / 1024

                    return `
                        <div class="zone-stacked-column">

                            <div class="zone-stacked-bars">

                                ${
                                    (snapshot.tags || [])
                                        .sort((a,b)=>b.bytes-a.bytes)
                                        .map(tag => {

                                            const height =
                                                (tag.bytes / max_total) * 400

                                            return `
                                                <div
                                                    class="zone-stacked-bar"
                                                    style="
                                                        height:${height}px
                                                    "
                                                    title="
${tag.tag}
${tag.mb.toFixed(2)} MB
                                                    "
                                                >
                                                </div>
                                            `
                                        }).join("")
                                }

                            </div>

                            <div class="zone-stacked-label">
                                ${snapshot.identifier || id}
                            </div>

                        </div>
                    `
                }).join("")
            }

        </div>
    `
}

function render_zone_chart()
{
    const zone_memory = document.querySelector('#zone_memory')
    const legend_el = document.querySelector('#zone_memory_legend')

    if (!zone_memory)
        return

    const snapshots =
        Object.values(
            zoneMemorySnapshots?.snapshots?.snapshots || {}
        )

    if (!snapshots.length)
        return

    const x =
        snapshots.map((_, i) => i)

    // gather all tags
    const tag_set = new Set()

    for (const snapshot of snapshots)
    {
        for (const tag of snapshot.tags || [])
            tag_set.add(tag.tag)
    }

    const tags =
        [...tag_set].sort()

    // uPlot data format
    const data = [x]

    // series config
    const series = [
        {}
    ]

    for (const tag_name of tags)
    {
        const values =
            snapshots.map(snapshot => {

                const tag =
                    (snapshot.tags || [])
                        .find(t => t.tag === tag_name)

                return tag
                    ? tag.mb
                    : 0
            })

        data.push(values)

        series.push({
            label: tag_name,
            stroke: tag_to_color(tag_name),
            width: 2,
        })
    }

    legend_el.innerHTML =
        tags.map((tag, i) => {

            const color =
                tag_to_color(tag)

            return `
                <div
                    class="legend-item"
                    data-series="${i + 1}"
                >
                    <span
                        class="legend-color"
                        style="background:${color}"
                    ></span>

                    <span class="legend-label">
                        ${tag}
                    </span>

                    <span class="legend-value">
                        0 MB
                    </span>
                </div>
            `
        }).join('')

    const options = {
        title: "Zone Memory Tags",
        width: zone_memory.clientWidth || 1000,
        height: 500,
        legend: {
            show: false,
        },
        axes: [
            {
            stroke: "#c9d1d9",
            grid: { stroke: "rgba(255,255,255,.08)" },
            ticks: { stroke: "#c9d1d9" },

            font: "12px Segoe UI",
            color: "#c9d1d9",
        },
        {
            stroke: "#c9d1d9",
            grid: { stroke: "rgba(255,255,255,.08)" },
            ticks: { stroke: "#c9d1d9" },

            font: "12px Segoe UI",
            color: "#c9d1d9",
        }
        ],
        scales: {
            x: {
                time: false,
            },
        },
        hooks: {
            setCursor: [
                u => {

                    const idx =
                        u.cursor.idx

                    if (idx == null)
                        return

                    for (let i = 1; i < u.series.length; i++)
                    {
                        const value =
                            u.data[i][idx]

                        const item =
                            legend_el.querySelector(
                                `[data-series="${i}"] .legend-value`
                            )

                        if (item)
                        {
                            item.textContent =
                                `${value} MB`
                        }
                    }
                }
            ]
        },
        series,
    }

    zone_memory.innerHTML = ""

    new uPlot(
        options,
        data,
        zone_memory
    )
}