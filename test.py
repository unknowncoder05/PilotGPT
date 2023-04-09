from developer.files.relevant import get_relevant_files
from developer.nodes.relevant import get_relevant_nodes
from developer.plan.steps import get_task_plan_steps, log_task_steps
from developer.nodes.new_nodes import get_new_nodes
from developer.nodes.from_file import get_file_nodes
from gpt.models import open_ai_model_func


def test_get_relevant_files():
    table_completion_gpt = open_ai_model_func("gpt-3.5-turbo", type="table_completion")
    relevant_files = get_relevant_files(table_completion_gpt, "make a function to get all prime numbers", files=["fibonacci.py", "primes.py", "cows.py", "random.js", "README.md"])
    assert "primes.py" in relevant_files

def test_get_file_nodes():
    table_completion_gpt = open_ai_model_func("gpt-3.5-turbo", type="table_completion")
    file_content = """def get_primes(n)
class Car:
Class Ford(Car):
Class Ferrari(Car):"""
    relevant_files = get_file_nodes(table_completion_gpt, file_content=file_content)
    print(relevant_files)
test_get_file_nodes()