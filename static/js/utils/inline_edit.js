async function update_environment_alias(env_id, alias)
{
    const data = await api_post("/update_environment_alias", {
        environment : env_id,
        alias       : alias,
    }, `update_environment_alias:${env_id}`)

    if (!data.success)
        console.log("Result:", data)
}

async function update_run_alias(env_id, run_id, alias)
{
    const data = await api_post("/update_run_alias", {
        environment : env_id,
        run_id      : run_id,
        alias       : alias,
    }, `update_run_alias:${env_id}_${run_id}`)

    if (!data.success)
        console.log("Result:", data)
}

const inlineEditors = {
    update_environment_alias(element) {
        update_environment_alias(
            element.dataset.envId,
            element.textContent.trim()
        );
    },

    update_run_alias(element) {
        update_run_alias(
            element.dataset.envId,
            element.dataset.runId,
            element.textContent.trim()
        );
    }
};

function initialize_inline_editors()
{
    document.querySelectorAll("[data-inline-edit]").forEach(create_inline_editor);
}

function create_inline_editor(element)
{
     if (element.dataset.inlineInitialized)
        return;

    element.contentEditable = "false";

    const edit = document.createElement("button");
    edit.innerHTML = '<i class="fa-solid fa-pen"></i>';
    edit.classList.add("edit")

    const save = document.createElement("button");
    save.innerHTML = '<i class="fa-solid fa-check"></i>';
    save.style.display = "none";

    const cancel = document.createElement("button");
    cancel.innerHTML = '<i class="fa-solid fa-xmark"></i>';
    cancel.style.display = "none";

    edit.onclick = () => begin_inline_edit(element);
    save.onclick = () => save_inline_edit(element);
    cancel.onclick = () => cancel_inline_edit(element);

    element.after(cancel);
    element.after(save);
    element.after(edit);

    element._inline = { edit, save, cancel };
    element.dataset.inlineInitialized = "true";
}

function begin_inline_edit(element)
{
    element.dataset.original = element.textContent;

    element.contentEditable = "true";
    element.focus();

    const range = document.createRange();
    range.selectNodeContents(element);

    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    element._inline.edit.style.display = "none";
    element._inline.save.style.display = "";
    element._inline.cancel.style.display = "";
}

function save_inline_edit(element)
{
    element.contentEditable = "false";

    const handler = inlineEditors[element.dataset.inlineEdit];
    if (handler)
        handler(element);

    element._inline.edit.style.display = "";
    element._inline.save.style.display = "none";
    element._inline.cancel.style.display = "none";
}

function cancel_inline_edit(element)
{
    element.textContent = element.dataset.original;
    element.contentEditable = "false";

    element._inline.edit.style.display = "";
    element._inline.save.style.display = "none";
    element._inline.cancel.style.display = "none";
}