import os
from developer.develop.develop import develop_task

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
        edited_file = develop_task(
            content=content,
            step=step,
            dependency_nodes=dependency_nodes,
            code_edit_gpt=code_edit_gpt,
            **step
        )

        file_name = step['file']
        if file_name.startswith("./"):
            file_name = file_name[2:]
        if file_name.startswith("/"):
            file_name = file_name[1:]
        yield file_name, edited_file
