from utils.dict_to_csv import dict_to_csv
from .optimize import optimize_code
from .human_readable_code import human_readable_code
from .bugs_in_code import bugs_in_code


def develop_task(
    content,
    dependency_nodes,
    file,
    node_type,
    name,
    code_edit_gpt,
    table_completion_gpt,
    inputs=[],
    outputs=[],
    parent_class=None,
    task_step_description=None,
    **kwargs
):
    rendered_dependency_nodes = dict_to_csv(dependency_nodes, headers=[
        "node_type", "name", "inputs", "outputs", "parent class", "short description", "file"], delimiter=';')
    exists = len(content) > 0
    if exists:
        instruction = f"""
current file: {file}
modify the {node_type} named {name}
inputs {inputs} 
outputs {outputs} 
parent class {parent_class} 
task: {task_step_description}
relevant resources:
{rendered_dependency_nodes}
"""
    else:
        instruction = f"""
current file: {file}
develop a {node_type} named {name}
inputs {inputs}
outputs {outputs}
parent class {parent_class}
task: {task_step_description}
relevant resources:
{rendered_dependency_nodes}
"""
    edited_file = code_edit_gpt(content, instruction, max_tokens=-1)
    edited_file = optimize_code(
        content=edited_file, node_type=node_type, name=name, code_edit_gpt=code_edit_gpt)
    edited_file = human_readable_code(
        content=edited_file, node_type=node_type, name=name, code_edit_gpt=code_edit_gpt)
    edited_file, solved_bugs = bugs_in_code(content=edited_file, node_type=node_type,
                                            name=name, code_edit_gpt=code_edit_gpt, table_completion_gpt=table_completion_gpt)
    return edited_file
