import hashlib
from .from_file_cache import get_file_nodes_cache, save_file_nodes_cache, CACHE_VERSION
from get_logger import logger

GET_NODES_PROMPT_FORMAT = """from the following file write the base resources 
Make sure that the classes that inherit from other classes get the field "parent class" filled
if the file is a code fiel, this are the types (variables, functions, function call, classes, loop, conditional...)
if the file is a documentation file, write the relevant sections of the documentation, this are the types (documentation, documentation section, documentation example...)
if the file is a requirements file, write the requirements, this are the types (requirements, command...)
file name:
{file_path}
```
{file_content}
```"""

def get_file_nodes(
        table_completion_gpt,
        file_path=None, file_content=None, use_cache=True, force_cache=False,
        headers=["node_type", "name", "inputs", "outputs", "parent class", "is parent", "short description", "methods"],
        verbose_headers=["node_type", "name", "inputs", "outputs", "is parent[True,False]", "parent class(the parent class of this class)", "short description", "methods:list"],
    ):
    # TODO: make sure file_path or file_content
    if not file_content:
        # TODO: set individual node hash
        with open(file_path) as f:
            file_content = f.read()
            file_hash = hashlib.sha256(file_content.encode()).hexdigest()

        # load cache if exists
        if use_cache and not force_cache:
            cashed_nodes = get_file_nodes_cache(file_path, file_hash=file_hash)
            if type(cashed_nodes) is list:
                logger.debug(f"Using cache for nodes in file {file_path}")
                return cashed_nodes

    # TODO: this might have the unintended consequence of leaving behind a  class called like "Utils" with tons of functionality
    #base_lines = [x for x in file_content.split("\n") if x.lstrip() == x and x]
    #top_nodes = len(base_lines)
    #if top_nodes == 0:
    #    return []
    if file_content =='':
        return []
    prompt = GET_NODES_PROMPT_FORMAT.format(file_path=file_path, file_content=file_content)
    file_nodes = table_completion_gpt(
        prompt, max_tokens=None,
        temperature=0,
        headers=headers,
        verbose_headers=verbose_headers,
    )
    nodes = []
    for raw_node in file_nodes:
        if raw_node.get('name') not in file_content:
            continue
        nodes.append(raw_node)

    # save cache
    if use_cache or force_cache:
        logger.debug(f"Saving cache for {file_path}")
        save_file_nodes_cache(file_path, nodes=nodes, file_hash=file_hash, version=CACHE_VERSION)

    return nodes
