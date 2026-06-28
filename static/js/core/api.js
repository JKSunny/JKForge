const active_requests = new Set()

function show_error(message, duration = 5000)
{
    let container = document.querySelector("#toast_container")

    if (!container) {
        container = document.createElement("div")
        container.id = "toast_container"

        document.body.appendChild(container)
    }

    const toast = document.createElement("div")

    toast.className = "toast toast-error"

    toast.innerHTML = `
        <i class="fa-solid fa-circle-exclamation"></i>
        <span>${message}</span>
    `

    container.appendChild(toast)

    requestAnimationFrame(() => {
        toast.classList.add("show")
    })

    setTimeout(() => {
        toast.classList.remove("show")

        setTimeout(() => {
            toast.remove()
        }, 200)

    }, duration)
}

function lock_request(key) {
    if (active_requests.has(key))
        return false

    active_requests.add(key)
    return true
}

function unlock_request(key) {
    active_requests.delete(key)
}

async function api_get(url, lock_key = null) {
    if (lock_key && !lock_request(lock_key))
        return { success: false, error: "Request already running" }

    try {
        const res = await fetch(url, {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        })

        const data = await res.json()

        if (!res.ok || !data.success)
            throw new Error(data.error || "Request failed")

        return data
    }

    catch (err) {
        console.error(`${url} failed:`, err)
        show_error(err.message)

        return {
            success: false,
            error: err.message
        }
    }

    finally {
        if (lock_key)
            unlock_request(lock_key)
    }
}

async function api_post(url, payload, lock_key = null) {
    if (lock_key && !lock_request(lock_key))
        return { success: false, error: "Request already running" }

    try {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })

        const data = await res.json()

        if (!res.ok || !data.success)
            throw new Error(data.error || "Request failed")

        return data
    }

    catch (err) {
        console.error(`${url} failed:`, err)

        show_error(err.message)

        return {
            success: false,
            error: err.message
        }
    }

    finally {
        if (lock_key)
            unlock_request(lock_key)
    }
}
