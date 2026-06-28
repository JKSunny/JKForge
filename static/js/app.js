function update_frontend(){
    render_environments_sidebar()
    render_selected_environment_modal();
}

setInterval(() => {
    update_frontend();
}, 1000)

;(function () {
    const config = get_window_config()

    if (config.http_use_socketio ?? false)
        connect_socket()
})()


render_no_run();