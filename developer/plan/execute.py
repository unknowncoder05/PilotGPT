import os
from utils.dict_to_csv import dict_to_csv

def execute_task_plan(code_edit_gpt, prompt, steps):
    for step in steps:
        if not step['file']:
            continue
        directory = os.path.dirname(step['file'])
        content = ""
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        elif os.path.exists(step['file']):
            with open(step['file'], 'r') as f:
                content = f.read()
        dependency_nodes = [dependency_node for dependency_node in steps if dependency_node['name'] in step['dependencies']]
        rendered_dependency_nodes = dict_to_csv(dependency_nodes, headers=[
                                     "type", "name", "inputs", "outputs", "parent class", "short description", "file"], delimiter=';')
        if step.get('exists'):
            instruction = f"""
current file: {step['file']}
modify the {step['type']} named {step['name']}
inputs {step['inputs']} 
outputs {step['outputs']} 
parent class {step['parent class']} 
task: {step['task_step_description']}
relevant resources:
{rendered_dependency_nodes}
"""
        else:
            instruction = f"""
current file: {step['file']}
code a {step['type']} named {step['name']} that {step['short description']}
inputs {step['inputs']} 
outputs {step['outputs']} 
parent class {step['parent class']} 
task: {step['task_step_description']}
relevant resources:
{rendered_dependency_nodes}
"""
        edited_file = code_edit_gpt(content, instruction, max_tokens=-1)

        file_name = step['file']
        if file_name.startswith("./"):
            file_name = file_name[2:]
        if file_name.startswith("/"):
            file_name = file_name[1:]
        yield file_name, edited_file
