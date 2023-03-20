from developer.task import Task
from project.project import Project
from gpt.models import open_ai_model_func
import os
import sys


if __name__ == '__main__':
    if len(sys.argv) < 4 + 1:
        print("Usage: python main.py <repository_url> <task_prompt> <input_branch> <output_branch>")
        sys.exit(1)
    repository_url = sys.argv[1]
    task_prompt = sys.argv[2]
    input_branch = sys.argv[3]
    output_branch = sys.argv[4]
    print(f"""repository_url={repository_url}
task_prompt={task_prompt}
input_branch={input_branch}
output_branch={output_branch}
"""
    )
    

    gpt = open_ai_model_func("text-davinci-002")
    code_edit_gpt = open_ai_model_func(
        "code-davinci-edit-001", type="code_edit")
    project = Project(repository_url=repository_url, repository_path='./repo', branch=input_branch)
    task = Task(
        gpt,
        code_edit_gpt,
        project=project,
        prompt=task_prompt,
    )
    task.plan(rexclude_files=['migrations', 'tests', '__pycache__',
                              '.git', 'media', '.env', 'node_modules', 'build', '.cache'])

    task.apply(target_branch=input_branch)
