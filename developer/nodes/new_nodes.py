# TODO: user dict to csv
def render_nodes_table(nodes_by_file, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description", "file"]):
    rendered_node_headers = ';'.join(headers)
    rendered_nodes_table = rendered_node_headers
    for file in nodes_by_file:
        for node in nodes_by_file[file]:
            rendered_nodes_table += '\n'
            rendered_nodes_table += ';'.join(node.values())+';'+file
    return rendered_nodes_table, rendered_node_headers


def get_new_nodes(gpt, prompt, nodes_by_file, headers=["type", "name", "file_name", "file_extension", "inputs", "outputs", "parent class", "is parent", "short description"], relevant_files_and_folders=None):
    GET_NEW_NODES_PROMPT_FORMAT = """from this nodes (variables, functions, classes, ...) add nodes that would need to be created to complete the task
- if none is required respond None, the file column is required
- make sure to give them a descriptive name
- give them a name that a senior developer would give
- use the "file" column to write the file where this node should be located
task:
{task}
relevant files and folders:
{relevant_files_and_folders}
nodes:
{nodes}
result:
{headers}
"""
    # TODO: let it know relevant directories
    # prompt
    rendered_nodes_table, _ = render_nodes_table(
        nodes_by_file)
    relevant_nodes_prompt = GET_NEW_NODES_PROMPT_FORMAT.format(
        task=prompt, nodes=rendered_nodes_table, headers=';'.join(headers), relevant_files_and_folders='\n'.join(relevant_files_and_folders))

    response = gpt(relevant_nodes_prompt, max_tokens=-1,
                   temperature=0)
    # clean response
    try:
        new_nodes = []
        for raw_new_node in response.split('\n'):
            attrs = [x.strip() for x in raw_new_node.split(';')]
            new_node = dict(zip(headers, attrs))
            file_extension = new_node.pop('file_extension')
            if file_extension and ('None' not in file_extension):
                if not file_extension.startswith('.'):
                    file_extension = '.' + file_extension
            else:
                file_extension  = ''
            file_name = new_node.pop('file_name')
            if not file_name.endswith(file_extension):
                file_name += file_extension
            new_node['file'] = file_name 
            new_nodes.append(
                new_node
            )
        return new_nodes
    except Exception as e:
        print('ERROR get_new_nodes', e)
