function short_commit(commit) 
{
    if (!commit) return ""
    return commit.substring(0, 8)
}

function splitArguments(input) 
{
    const result = []
    const regex = /[^\s"]+|"([^"]*)"/gi

    let match

    while ((match = regex.exec(input)) !== null)
        result.push(match[1] ?? match[0])

    return result
}

function normalizeRendererName(value) 
{
    return value
        .toLowerCase()
        .replace(/^rd-/, "")
        .replace(/renderer/g, "")
        .replace(/vanilla/g, "")
        .trim()
}