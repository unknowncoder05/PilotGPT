from project.project import Project
from developer.clarifications import get_task_clarifications
from developer.plan.task_plan import get_task_plan
from developer.plan.execute import execute_task_plan
from developer.plan.steps import print_task_steps


class Task:
    project: Project
    prompt: str
    commit_message: str
    planned: bool = False

    # TODO: proper types
    def __init__(self, gpt, code_edit_gpt, project: Project, prompt, commit_message=None) -> None:
        self.gpt = gpt
        self.code_edit_gpt = code_edit_gpt
        self.project = project
        self.prompt = prompt

        if commit_message == None:
            self.commit_message = prompt
        else:
            # TODO: make gpt create a good name
            self.commit_message = commit_message
        pass

    def plan(self, ask_for_clarifications=False, exclude_files=[], rexclude_files=[]):
        if ask_for_clarifications:
            clarifications = get_task_clarifications(self.gpt, self.prompt)
            print(clarifications)
            return

        steps = get_task_plan(self.gpt, self.prompt, self.project.repository_path,
                              exclude_files=exclude_files, rexclude_files=rexclude_files)
        self.steps = steps
        self.planned = True
        return steps

    def apply(self, ask_confirmation=True, target_branch=None, push=True, origin_name='origin'):
        if not self.planned:
            raise Exception("you have to plan this task before executing it")
        
        # print plan and ask for confirmation
        if ask_confirmation:
            print_task_steps(self.steps)
            confirmation = input("apply (y,N)") == "y"
            if not confirmation:
                return
        
        # save the name of the current branch
        current_branch = self.project.repo.active_branch.name

        # create a new branch and switch to it
        new_branch = self.project.repo.create_head(target_branch)
        self.project.repo.head.reference = new_branch
        self.project.repo.head.reset(index=True, working_tree=True)

        print('STEPS:', self.steps)
        # modify files
        edited_files = []
        for file_name, file_edited_content in execute_task_plan(self.code_edit_gpt, self.prompt, self.steps):
            # TODO: use join path
            with open(file_name, 'w') as f:
                f.write(file_edited_content)
            # stage changes
            edited_files.append(file_name)
        
        # stage and commit changes
        self.project.repo.index.add(edited_files)
        commit_message = self.commit_message
        self.project.repo.index.commit(commit_message)

        # push
        if push:
            origin = self.project.repo.remote(name=origin_name)
            origin.push()

        # switch back to the original branch
        original_branch = self.project.repo.branches[current_branch]
        original_branch.checkout()

