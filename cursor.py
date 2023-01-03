import ast
import re
import openai
import os


def check_content_filter(prompt):
    completions = openai.Completion.create(
        engine="content-filter-alpha",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        top_p=0
    )
    return completions.choices[0].text


def execute_completion_model(prompt, model="code-davinci-002", temperature=1, max_tokens=100, many=False, *args, **kwargs):
    """
    Executes the completion model with the given parameters and returns the list of responses.
    """
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        *args, **kwargs
    )
    if many:
        return [x.text.strip() for x in response.choices]
    else:
        return response.choices[0].text.strip()


def open_ai_model_func(model, type='completion'):
    """
    Returns a function that executes the given model with the specified type.
    """
    if type == 'completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute
    if type == 'code_completion':
        def execute(prompt_text, *args, **kwargs):
            return execute_completion_model(prompt_text, model=model, *args, **kwargs)
        return execute

# utils
def list_py_files(dir_path: str):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)

def node_verbose_definition(node, indent: str = '') -> str:
    result = ''
    if isinstance(node, ast.Import):
        for alias in node.names:
            result += f'{indent}import {alias.name}'
            if alias.asname:
                result += f' as {alias.asname}'
            result += '\n'
    elif isinstance(node, ast.ImportFrom):
        result += f'{indent}from {node.module} import '
        result += ', '.join([alias.name for alias in node.names])
        result += '\n'
    elif isinstance(node, ast.Assign):
        result += f'{indent}'
        print(">>>>>>>><",' = '.join([node_verbose_definition(target) for target in node.targets]))
        result += ' = '.join([node_verbose_definition(target) for target in node.targets])
        result += f' = {node_verbose_definition(node.value)}\n'
    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        is_async = isinstance(node, ast.AsyncFunctionDef)
        result += f'{indent}'
        result += ''.join(["@"+node_verbose_definition(decorator)+"\n" for decorator in node.decorator_list])
        result += "async " if is_async else ""
        result += f'def {node.name} ('
        result += ', '.join([node_verbose_definition(arg) for arg in node.args.args])
        result += f') -> {node_verbose_definition(node.returns)}:\n'
    elif isinstance(node, ast.ClassDef):
        bases = f"({', '.join([x.id for x in node.bases])})" if node.bases else ""
        result += f'{indent}class {node.name}{bases}:\n'
        for child in node.body:
            result += node_verbose_definition(child, indent + '    ')+"\n"
    elif isinstance(node, ast.Name):
        result += node.id
    elif isinstance(node, ast.Str):
        result += repr(node.s)
    elif isinstance(node, ast.Num):
        result += repr(node.n)
    elif isinstance(node, ast.Tuple):
        result += '('
        result += ', '.join([node_verbose_definition(elt) for elt in node.elts])
        result += ')'
    elif isinstance(node, ast.List):
        result += '['
        result += ', '.join([node_verbose_definition(elt) for elt in node.elts])
        result += ']'
    elif isinstance(node, ast.Dict):
        result += '{'
        result += ', '.join([f'{node_verbose_definition(key)}: {node_verbose_definition(value)}' for key, value in zip(node.keys, node.values)])
        result += '}'
    elif isinstance(node, ast.AnnAssign):
        result += indent+node.target.id + ":" + node.annotation.id
        
    elif isinstance(node, ast.Expr):
        print(ast.Expr, vars(node))
    
    elif isinstance(node, ast.Attribute):  # Add this case
        result = ''
        result += node_verbose_definition(node.value)
        result += '.'
        result += node_verbose_definition(node.attr)
        return result
        
    elif isinstance(node, ast.Call):  # Add this case
        result = ''
        result += node_verbose_definition(node.func)
        result += '('
        result += ', '.join([node_verbose_definition(arg) for arg in node.args])
        result += ')'
        return result
    elif isinstance(node, str):  # Add this case
        return node
    elif isinstance(node, ast.arg):  # Add this case
        result = ''
        result += node_verbose_definition(node.arg)
        if node.annotation is not None:
            result += ': '
            result += node_verbose_definition(node.annotation)
        return result
    elif isinstance(node, ast.Module):
        for child in ast.iter_child_nodes(node):
            result += node_verbose_definition(child, indent)
        return result
    elif node is None:
        return 'None'
    else:
        pass
        #print(type(node))
    return result

def tree_node_verbose_definition(file_path: str):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    result = node_verbose_definition(tree)
    return result

TASK_CLARIFICATIONS = """
"""

openai.api_key = os.getenv("OPENAPI_API_KEY")
gpt = open_ai_model_func("text-davinci-002")


def fulfill_task(prompt, target_dir):
    clarifications = TASK_CLARIFICATIONS.format(prompt=prompt)
    files = list_py_files(target_dir)
    for file_name in files:
        nodes = tree_node_verbose_definition(file_name)
        print(len(nodes))


if __name__ == '__main__':
    fulfill_task("add an endpoint that returns server side",
                 '/home/unknown-dev/Desktop/storage/YERSON/Personal/ProjetD/text-game/backend/app')
