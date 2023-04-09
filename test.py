from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.plan.steps import get_task_plan_steps, log_task_steps
from developer.nodes.new_nodes import get_new_nodes
from developer.nodes.from_file import get_file_nodes
from gpt.models import open_ai_model_func


def test_get_relevant_files():
    table_completion_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="table_completion")
    task_prompts = "make a function to get all prime numbers"
    relevant_files = get_relevant_files(table_completion_gpt, task_prompts, files=[
                                        "fibonacci.py", "primes.py", "cows.py", "random.js", "README.md"])
    assert "primes.py" in relevant_files


def test_get_file_nodes():
    table_completion_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="table_completion")
    file_content = """def get_primes(n)
class Car:
Class Ford(Car):
Class Ferrari(Car):"""
    relevant_file_nodes = get_file_nodes(
        table_completion_gpt, file_content=file_content)


def test_get_relevant_nodes():
    selection_gpt = open_ai_model_func("gpt-3.5-turbo", type="selection_gpt")
    task_prompts = "make a function to get all prime numbers"
    nodes_by_file = [('./main.py', [
        {'type': 'function', 'name': 'get_primes', 'inputs': 'n', 'outputs': 'int[]', 'parent class': '',
                                     'is parent': 'False', 'short description': 'A function that returns an array of prime numbers up to n.'},
        {'type': 'class', 'name': 'Car', 'inputs': '', 'outputs': '', 'parent class': 'object',
         'is parent': 'True', 'short description': 'A class that represents a car.'},
        {'type': 'class', 'name': 'Ford', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ford car and inherits from the Car class.'},
        {'type': 'class', 'name': 'Ferrari', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ferrari car and inherits from the Car class.'}
    ])]
    relevant_nodes = get_relevant_nodes(
        task_prompts, selection_gpt=selection_gpt, table_completion_gpt=None, nodes_by_file=nodes_by_file)
    print(relevant_nodes)

def test_get_new_nodes():
    table_completion = open_ai_model_func("gpt-3.5-turbo", type="table_completion")
    task_prompts = "add a lamborghini car class that has a price of one million dollars"
    nodes = [
        {'file': './car.py', 'type': 'class', 'name': 'Car', 'inputs': '', 'outputs': '', 'parent class': 'object',
         'is parent': 'True', 'short description': 'A class that represents a car.'},
        {'file': './cars/Ford.py', 'type': 'class', 'name': 'Ford', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ford car and inherits from the Car class.'},
        {'file': './cars/Ferrari.py', 'type': 'class', 'name': 'Ferrari', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ferrari car and inherits from the Car class.'}
    ]
    relevant_files_and_folders = ['./car.py', './cars', './cars/Ford.py', './cars/Ferrari.py']
    relevant_nodes = get_new_nodes(
        task_prompts, nodes, table_completion_gpt=table_completion, relevant_files_and_folders=relevant_files_and_folders)
    print(relevant_nodes)


test_get_new_nodes()
