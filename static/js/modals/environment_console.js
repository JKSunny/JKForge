let envConsoleOutput = {}
let envConsoleFollowBottom = true
let envConsoleAbort

function env_console_key(env_id) {
    return `${env_id}`
}

function env_console_scroll_init()
{
    const env_console = document.querySelector('#env_console')

    if (!env_console)
        return

    envConsoleAbort = new AbortController()
    
    env_console.addEventListener('scroll', () => 
    {
        const threshold = 5
        envConsoleFollowBottom =
        env_console.scrollHeight - env_console.scrollTop - env_console.clientHeight <= threshold
    }, 
    { signal: envConsoleAbort.signal })
}

function env_console_scroll_update()
{
    const env_console = document.querySelector('#env_console')

    if (!env_console)
        return

    const oldScrollTop = env_console.scrollTop
    const wasAtBottom = envConsoleFollowBottom

    if (wasAtBottom)
        env_console.scrollTop = env_console.scrollHeight
    else
        env_console.scrollTop = oldScrollTop
}

function env_console_scroll_destroy()
{
    envConsoleAbort?.abort()
    envConsoleAbort = null
}

function render_env_console()
{
    const env_console = document.querySelector('#env_console')

    if (!env_console)
        return

    const key = env_console_key(selectedEnvironmentId)

    const text = envConsoleOutput[key] || ""
    env_console.textContent = text

    env_console_scroll_update()
}

async function init_env_console_history() 
{
    const data = await api_post(
        "/get_env_console",
        {
            environment: selectedEnvironmentId,
        },
        `get_env_console:${selectedEnvironmentId}:`
    )

    if (!data.success)
        return

    const key = env_console_key(selectedEnvironmentId)
    envConsoleOutput[key] = data.content

    render_env_console()
    env_console_scroll_init()
}

function clear_env_console()
{
    const key = env_console_key(selectedEnvironmentId)

    envConsoleOutput[key] = ""

    env_console_scroll_destroy()
}

function append_env_console( data )
{
    const key = env_console_key(data.environment)

    if (!envConsoleOutput[key])
        envConsoleOutput[key] = ""

    envConsoleOutput[key] += data.append

    if ( data.environment === selectedEnvironmentId ) {
        render_env_console()
    }
}

function redraw_env_console( data )
{
    if ( data.environment === selectedEnvironmentId ) {
        clear_env_console()
        init_env_console_history()
    }
}