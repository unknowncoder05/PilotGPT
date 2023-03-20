# TODO: user dict to csv
def render_nodes_table(nodes_by_file, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description", "file"]):
    rendered_node_headers = ';'.join(headers)
    rendered_nodes_table = rendered_node_headers
    for file in nodes_by_file:
        for node in nodes_by_file[file]:
            rendered_nodes_table += '\n'
            rendered_nodes_table += ';'.join(node.values())+';'+file
    return rendered_nodes_table, rendered_node_headers

def get_new_nodes(gpt, prompt, nodes_by_file, headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description", "file"], relevant_files_and_folders=None):
    GET_NEW_NODES_PROMPT_FORMAT = """from this nodes (variables, functions, classes, ...) add nodes that would need to be created to complete the task
- if none is required respond None
- make sure to give them a descriptive name
- give them a name that a senior developer would give
- create them in files that can then be reused
- add the file where the new node will be created
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
    rendered_nodes_table, rendered_node_headers = render_nodes_table(
        nodes_by_file)
    relevant_nodes_prompt = GET_NEW_NODES_PROMPT_FORMAT.format(
        task=prompt, nodes=rendered_nodes_table, headers=rendered_node_headers, relevant_files_and_folders='\n'.join(relevant_files_and_folders))

    response = gpt(relevant_nodes_prompt, max_tokens=-1,
                   temperature=0)
    # clean response
    try:
        new_nodes = []
        for new_node in response.split('\n'):
            attrs = [x.strip() for x in new_node.split(';')]
            new_nodes.append(
                dict(zip(headers, attrs))
            )
        return new_nodes
    except Exception as e:
        print('ERROR get_new_nodes', e)