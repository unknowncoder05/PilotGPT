def optimize_code(
    content,
    node_type,
    name,
    code_edit_gpt,
):
    instruction = f"""optimize this function
reduce the complexity of the algorithms used if applies
reduce the memory usage if applies
don't remove any of the previously created resources or change their inputs and outputs
{node_type} {name}: {content}
"""
    edited_file = code_edit_gpt(content, instruction, max_tokens=-1)
    return edited_file
