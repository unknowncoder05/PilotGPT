from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.plan.steps import get_task_plan_steps, log_task_steps
from developer.nodes.new_nodes import get_new_nodes
from developer.nodes.from_file import get_file_nodes
from gpt.models import open_ai_model_func

from developer.develop.develop import develop_task
from developer.develop.optimize import optimize_code
from developer.develop.human_readable_code import human_readable_code
from developer.develop.bugs_in_code import bugs_in_code


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
        {'node_type': 'function', 'name': 'get_primes', 'inputs': 'n', 'outputs': 'int[]', 'parent class': '',
         'is parent': 'False', 'short description': 'A function that returns an array of prime numbers up to n.'},
        {'node_type': 'class', 'name': 'Car', 'inputs': '', 'outputs': '', 'parent class': 'object',
         'is parent': 'True', 'short description': 'A class that represents a car.'},
        {'node_type': 'class', 'name': 'Ford', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ford car and inherits from the Car class.'},
        {'node_type': 'class', 'name': 'Ferrari', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ferrari car and inherits from the Car class.'}
    ])]
    relevant_nodes = get_relevant_nodes(
        task_prompts, selection_gpt=selection_gpt, table_completion_gpt=None, nodes_by_file=nodes_by_file)


def test_get_new_nodes():
    table_completion = open_ai_model_func(
        "gpt-3.5-turbo", type="table_completion")
    task_prompts = "add a lamborghini car class that has a price of one million dollars"
    nodes = [
        {'file': './car.py', 'node_type': 'class', 'name': 'Car', 'inputs': '', 'outputs': '', 'parent class': 'object',
         'is parent': 'True', 'short description': 'A class that represents a car.'},
        {'file': './cars/Ford.py', 'node_type': 'class', 'name': 'Ford', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ford car and inherits from the Car class.'},
        {'file': './cars/Ferrari.py', 'node_type': 'class', 'name': 'Ferrari', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ferrari car and inherits from the Car class.'}
    ]
    relevant_files_and_folders = [
        './car.py', './cars', './cars/Ford.py', './cars/Ferrari.py']
    relevant_nodes = get_new_nodes(
        task_prompts, nodes, table_completion_gpt=table_completion, relevant_files_and_folders=relevant_files_and_folders)
    # [{'node_type': 'class', 'name': 'Lamborghini', 'inputs': '', 'outputs': 'price', 'is parent': 'Car', 'parent class': 'True', 'short description': 'A class that represents a Lamborghini car and inherits from the Car class.', 'file': 'Lamborghini.py'}]


def test_get_task_plan_steps():
    table_completion = open_ai_model_func(
        "gpt-3.5-turbo", type="table_completion")
    task_prompts = "add a lamborghini car class that has two doors"
    nodes = [
        {'file': './car.py', 'node_type': 'class', 'name': 'Car', 'inputs': '', 'outputs': '', 'parent class': 'object',
         'is parent': 'True', 'short description': 'A class that represents a car.'},
        {'file': './cars/Ford.py', 'node_type': 'class', 'name': 'Ford', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ford car and inherits from the Car class.'},
        {'file': './cars/Ferrari.py', 'node_type': 'class', 'name': 'Ferrari', 'inputs': '', 'outputs': '', 'parent class': 'Car', 'is parent': 'True',
         'short description': 'A class that represents a Ferrari car and inherits from the Car class.'}
    ]
    new_nodes = [{'node_type': 'class', 'name': 'Lamborghini', 'inputs': '', 'outputs': '', 'is parent': 'Car', 'parent class': 'True',
                  'short description': 'A class that represents a Lamborghini car and inherits from the Car class.', 'file': 'Lamborghini.py'}]
    relevant_nodes = get_task_plan_steps(
        task_prompts, nodes, new_nodes, table_completion_gpt=table_completion)
    log_task_steps(relevant_nodes)


def test_develop_task():
    task_prompt = "make a function that gets the nth prime number"
    task_step_description = task_prompt
    code_edit_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="code_edit")
    file = develop_task(
        content=task_prompt,
        dependency_nodes=[],
        file="primes.py",
        exists=False,
        node_type="function",
        name="get_nth_prime",
        inputs=["n:int"],
        outputs=["prime:int"],
        parent_class=None,
        task_step_description=task_step_description,
        code_edit_gpt=code_edit_gpt,
    )
    print(file)


def test_optimize_code():
    code = '''def get_nth_prime(n):
    """
    Returns the nth prime number using brute force.
    """
    primes = [2]  # start with the first prime number
    num = 3  # start checking for primes from 3
    
    while len(primes) < n:
        is_prime = True  # assume num is prime
        for prime in primes:
            if num % prime == 0:
                is_prime = False  # num is not prime
                break
        if is_prime:
            primes.append(num)  # add num to the list of primes
        num += 1  # move on to the next number
    
    return primes[-1]  # return the last (nth) prime number'''
    code_edit_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="code_edit")
    file = optimize_code(
        content=code,
        node_type="function",
        name="get_nth_prime",
        code_edit_gpt=code_edit_gpt,
    )
    print(file)


def test_human_readable_code():
    code = '''def get_nth_prime(n):
    """
    Returns the nth prime number using brute force.
    """
    if n == 1:
        return 2
    primes = [2]  # start with the first prime number
    num = 3  # start checking for primes from 3
    
    while len(primes) < n:
        is_prime = True  # assume num is prime
        for prime in primes:
            if prime * prime > num:
                break
            if num % prime == 0:
                is_prime = False  # num is not prime
                break
        if is_prime:
            primes.append(num)  # add num to the list of primes
        num += 2  # move on to the next odd number
    
    return primes[-1]  # return the last (nth) prime number'''
    code_edit_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="code_edit")
    file = human_readable_code(
        content=code,
        node_type="function",
        name="get_nth_prime",
        code_edit_gpt=code_edit_gpt,
    )
    print(file)

def test_bugs_in_code():
    code = '''def get_nth_prime(n: int) -> int:
    """
    Returns the nth prime number using brute force.

    Args:
    n (int): the nth prime number to be returned.

    Returns:
    int: the nth prime number.

    """
    if n == 1:
        return 2
    primes = [2]  # start with the first prime number
    num = 3  # start checking for primes from 3
    
    while len(primes) < n:
        is_prime = True  # assume num is prime
        for prime in primes:
            if prime * prime > num:
                break
            if num % prime == 0:
                is_prime = False  # num is not prime
                break
        if is_prime:
            primes.append(num)  # add num to the list of primes
        num += 2  # move on to the next odd number
    
    return primes[-1]  # return the last (nth) prime number'''
    code_edit_gpt = open_ai_model_func(
        "gpt-3.5-turbo", type="code_edit")
    table_completion_gpt = open_ai_model_func(
            "gpt-3.5-turbo", type="table_completion")
    file = bugs_in_code(
        content=code,
        node_type="function",
        name="get_nth_prime",
        code_edit_gpt=code_edit_gpt,
        table_completion_gpt=table_completion_gpt,
    )
    print(file)


# def test_implement_tests_code():
#     code = '''def get_nth_prime(n: int) -> int:
#     """
#     Returns the nth prime number using Sieve of Eratosthenes algorithm.

#     Args:
#     n (int): the nth prime number to be returned.

#     Returns:
#     int: the nth prime number.

#     """
#     if not isinstance(n, int) or n <= 0:
#         raise ValueError("n must be a positive integer")
#     if n == 1:
#         return 2
#     primes = [2]  # start with the first prime number
#     num = 3  # start checking for primes from 3
#     while len(primes) < n:
#         is_prime = True  # assume num is prime
#         for prime in primes:
#             if prime * prime > num:
#                 break
#             if num % prime == 0:
#                 is_prime = False  # num is not prime
#                 break
#         if is_prime:
#             primes.append(num)  # add num to the list of primes
#         num += 2  # move on to the next odd number
#     return primes[-1]  # return the last (nth) prime number'''
#     code_edit_gpt = open_ai_model_func(
#         "gpt-3.5-turbo", type="code_edit")
#     table_completion_gpt = open_ai_model_func(
#             "gpt-3.5-turbo", type="table_completion")
#     file = bugs_in_code(
#         content=code,
#         node_type="function",
#         name="get_nth_prime",
#         code_edit_gpt=code_edit_gpt,
#         table_completion_gpt=table_completion_gpt,
#     )
#     print(file)

test_bugs_in_code()
