import hashlib
from developer.nodes.from_file_cache import get_file_nodes_cache, save_file_nodes_cache

def get_file_nodes(gpt, file_path, use_cache=True, splitter=';', headers=["type", "name", "inputs", "outputs", "parent class", "is parent", "short description"]):
    GET_NODES_PROMPT_FORMAT = """from this file write the base nodes (variables, functions, function call, classes, ...) that would need to be modified
- for fields that don't apply to the node type, left an empty space None
- separate list fields by commas ','
- for inputs and outputs use format 'name:type' if a list, add the type of it's items
>>>
{file_content}
<<<
parent nodes: 
{headers}
"""
    # TODO: set individual node hash
    with open(file_path) as f:
        file_content = f.read()
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()

    # load cache if exists
    if use_cache:
        cashed_nodes = get_file_nodes_cache(file_path, file_hash=file_hash)
        if type(cashed_nodes) is list:
            return cashed_nodes

    # raw get nodes
    base_lines = [x for x in file_content.split("\n") if x.lstrip() == x and x]
    prompt = GET_NODES_PROMPT_FORMAT.format(
        file_content="\n".join(base_lines), headers=splitter.join(headers))
    result = gpt(prompt, max_tokens=-1,
                 temperature=0, stop=['parent nodes:', 'child nodes:'])
    nodes = [dict(zip(headers, x.split(splitter))) for x in result.split('\n')]

    # save cache
    if use_cache:
        save_file_nodes_cache(file_path, nodes=nodes, file_hash=file_hash)

    return nodes