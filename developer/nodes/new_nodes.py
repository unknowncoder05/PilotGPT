from get_logger import logger
import os


def get_new_nodes(prompt, nodes, table_completion_gpt,
                  headers=["node_type", "file_directory_path", "file_name", "file_extension", "name", "short description", "inputs",
                           "outputs", "is parent", "parent class", "methods"],
                  verbose_headers=["node_type", "file_directory_path(required, make it descriptive)", "file_name(required)", "file_extension(required)", "name(required)", "short description",
                                   "inputs(leave blank if class nodes)", "outputs(leave blank if class nodes)", "is parent[one of True,False]", "parent class(the class from which it inherits)", "methods: list"],
                  relevant_files_and_folders=None
    ):
    GET_NEW_NODES_PROMPT_FORMAT = """from this resources (variables, functions, classes, ...) add resources that would need to be created to complete the task: {prompt}"""
    extra_requirements = [
        "the name of the resource should represent it's functionalities and not be repeated if one already exists",
        "create new resources on already existing folders related to it's functionalities",
        "follow the file structure for the file_directory_path and file_name (give them descriptive names)",
        "if an other resource with the same functionalities exists, do not add a new one",
    ]
    # TODO: let it know relevant directories
    # prompt
    new_nodes_prompt = GET_NEW_NODES_PROMPT_FORMAT.format(prompt=prompt)
    raw_new_nodes = table_completion_gpt(
        new_nodes_prompt,
        max_tokens=None,
        temperature=0,
        headers=headers,
        verbose_headers=verbose_headers,
        context_tables=[
            {
                "name": "related resources",
                "data": nodes
            },
            {
                "name": "related files and folders",
                # TODO: make this more developer friendly
                "data": [{"path": relevant_path} for relevant_path in relevant_files_and_folders]
            },
        ],
        extra_requirements=extra_requirements
    )
    logger.debug(f"raw_new_nodes: {raw_new_nodes}")
    # clean response
    try:
        # TODO: make it yield
        new_nodes = []
        for raw_new_node in raw_new_nodes:
            new_node = raw_new_node.copy()
            # get proper file full name
            file_extension = new_node.pop('file_extension')
            if file_extension and ('None' not in file_extension):
                if not file_extension.startswith('.'):
                    file_extension = '.' + file_extension
            else:
                file_extension = ''
            file_directory_path = new_node.pop('file_directory_path')
            
            # sometimes the LLM returns the whole path here
            if os.path.isfile(file_directory_path):
                new_node['file'] = file_directory_path
            else:
                file_name = new_node.pop('file_name')
                if not file_name.endswith(file_extension):
                    file_name += file_extension
                new_node['file'] = os.path.join(file_directory_path, file_name)
            new_nodes.append(
                new_node
            )
        return new_nodes
    except Exception as e:
        logger.error(e)
