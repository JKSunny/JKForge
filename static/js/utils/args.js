function splitArguments(input) {
    const result = []
    const regex = /[^\s"]+|"([^"]*)"/gi

    let match

    while ((match = regex.exec(input)) !== null)
        result.push(match[1] ?? match[0])

    return result
}
