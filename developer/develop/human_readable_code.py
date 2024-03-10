def human_readable_code(
    content,
    node_type,
    name,
    code_edit_gpt,
):
    instruction = f"""make this code human readable
add relevant comments
add relevant documentation to the start of every resource like the meaning of arguments and outputs in functions 
add proper typing to inputs and outputs if applies
write comments with possible improvements as TODOs
don't change the base logic
don't remove any of the previously created resources or change their inputs and outputs
add documentation of the inputs and outputs
{node_type} {name}: {content}
"""
    edited_file = code_edit_gpt(content, instruction, max_tokens=None)
    return edited_file
