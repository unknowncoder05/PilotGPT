from developer.task import Task
from project.project import Project
from gpt.models import open_ai_model_func
import os


if __name__ == '__main__':
    gpt = open_ai_model_func("text-davinci-002")
    code_edit_gpt = open_ai_model_func(
        "code-davinci-edit-001", type="code_edit")
    project = Project(repository_path=os.getenv("REPOSITORY_PATH"))
    task = Task(gpt, code_edit_gpt, project=project,
                prompt="add a Sieve of Eratosthenes method to find primes",
                )
    task.plan(rexclude_files=['migrations', 'tests', '__pycache__',
                              '.git', 'media', '.env', 'node_modules', 'build', '.cache'])

    task.apply(target_branch='TASK-1')
