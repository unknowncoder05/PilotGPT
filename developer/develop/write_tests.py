from utils.dict_to_csv import dict_to_csv
import os

def find_test_directory(path):
    """Find the test directory for a given project path.

    Args:
        path (str): The path to the project.

    Returns:
        Tuple: The path to the test directory if found and a boolean indicating whether the tests are in a separate directory or not.
    """
    test_dirs = [
        "tests",
        "test",
        "testing",
        "unittests",
        "specs",
        "features",
        "scenarios",
    ]
    for directory in test_dirs:
        test_path = os.path.join(path, directory)
        if os.path.isdir(test_path):
            return (test_path, True)
    for root, dirs, files in os.walk(path):
        for filename in files:
            if 'test' in filename.lower():
                return (root, False)
    return (None, False)

def write_tests(
        test_file_content,
        content,
        file,
        exists,
        node_type,
        name,
        inputs=[],
        outputs=[],
        parent_class=None,
        code_edit_gpt=None,
        **kwargs
    ):
    if exists:
        action = f"modify the tests for the {node_type} {name}"
    else:
        action = f"create the tests for the {node_type} {name}"
    instruction = f"""current file: {file}
{action}
inputs {inputs} 
outputs {outputs} 
parent class {parent_class} 
{node_type} {name}: {content}
"""
    edited_file = code_edit_gpt(test_file_content, instruction, max_tokens=-1)
    return edited_file