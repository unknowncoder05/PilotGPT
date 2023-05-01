from utils.dict_to_csv import dict_to_csv

def develop_task(
        content,
        dependency_nodes,
        file,
        node_type,
        name,
        inputs=[],
        outputs=[],
        parent_class=None,
        task_step_description=None,
        code_edit_gpt=None,
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
    return edited_file