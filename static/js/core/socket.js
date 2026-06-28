let socket;

function socket_join_run( run_id )
{
    if (!socket || !socket.connected) {
        console.error("Socket not connected");
        return;
    }

    if (run_id) {
        socket.emit('join_run', {
            run: run_id
        })
    }
}

function socket_leave_run( run_id )
{
    if (!socket || !socket.connected) {
        console.error("Socket not connected");
        return;
    }
    console.log(run_id);
    if (run_id) {
        socket.emit('leave_run', {
            run: run_id
        })
    }
}

function socket_join_env_detail( env_id )
{
    if (!socket || !socket.connected) {
        console.error("Socket not connected");
        return;
    }

    if (env_id) {
        socket.emit('join_env_detail', {
            env: env_id
        })
    }
}

function socket_leave_env_detail( env_id )
{
    if (!socket || !socket.connected) {
        console.error("Socket not connected");
        return;
    }

    if (env_id) {
        socket.emit('laeve_env_detail', {
            run: env_id
        })
    }
}

function connect_socket() 
{
    socket = io()

    socket.on("connect", () => {
        console.log("Connected to server")
    })

    socket.on("fetch_state", (data) => {
        current_environments = data.environments || []
        
        update_frontend();
    })

    socket.on("qconsole_append", (data) => {
        append_qconsole( data )
    })

    socket.on("env_console_append", (data) => {
        append_env_console( data )
    })

    socket.on("env_console_redraw", (data) => {
        redraw_env_console( data )
    })

    socket.on("config_updated", (config) => {
        set_window_config( config )
    })
}
