function get_client( name )
{
    const config = get_window_config()
    const client = config.clients_meta?.find(e => e.name === name)

    return client ?? {}
}
