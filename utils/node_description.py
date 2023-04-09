import ast


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
        result += ' = '.join([node_verbose_definition(target)
                             for target in node.targets])
        result += f' = {node_verbose_definition(node.value)}\n'
    elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        is_async = isinstance(node, ast.AsyncFunctionDef)
        result += f'{indent}'
        result += ''.join(["@"+node_verbose_definition(decorator) +
                          "\n" for decorator in node.decorator_list])
        result += "async " if is_async else ""
        result += f'def {node.name} ('
        result += ', '.join([node_verbose_definition(arg)
                            for arg in node.args.args])
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
        result += ', '.join([node_verbose_definition(elt)
                            for elt in node.elts])
        result += ')'
    elif isinstance(node, ast.List):
        result += '['
        result += ', '.join([node_verbose_definition(elt)
                            for elt in node.elts])
        result += ']'
    elif isinstance(node, ast.Dict):
        result += '{'
        result += ', '.join([f'{node_verbose_definition(key)}: {node_verbose_definition(value)}' for key,
                            value in zip(node.keys, node.values)])
        result += '}'
    elif isinstance(node, ast.AnnAssign):
        result += indent+node.target.id + ":" + node.annotation.id

    # elif isinstance(node, ast.Expr):  # Add this case
    #    return node_verbose_definition(node.value)

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
        result += ', '.join([node_verbose_definition(arg)
                            for arg in node.args])
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
    return result


def tree_node_verbose_definition(file_path: str):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    result = node_verbose_definition(tree)
    return result


def get_node_names_and_types(node):
    #elif isinstance(node, ast.Assign):
    #    for target in node.targets:
    #        result.append(node_verbose_definition(target) + ' assignment')
    if isinstance(node, ast.FunctionDef):
        return (node.name + ' function')
    if isinstance(node, ast.AsyncFunctionDef):
        return (node.name + ' function')
    elif isinstance(node, ast.ClassDef):
        return (node.name + ' class')
    elif isinstance(node, ast.Name):
        return (node.id + ' name')


def tree_node_names(file_path: str):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    total_nodes = []
    for node in ast.iter_child_nodes(tree):
        nodes = get_node_names_and_types(node)
        if nodes:
            total_nodes.append(nodes)
    return total_nodes
