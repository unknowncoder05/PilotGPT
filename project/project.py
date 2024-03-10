import git
from git import Repo
from utils.list_files_recursively import list_files_recursively
from .nodes.from_file import get_file_nodes

def clone_repository(repository_url, target_dir, branch="main"):
    repo = git.Repo.clone_from(repository_url, target_dir, branch=branch)
    return repo


class Project:
    repository_url: str
    repository_path: str
    repo: Repo

    def __init__(self, repository_path=None, repository_url=None, branch="main") -> None:
        self.repository_url = repository_url
        self.repository_path = repository_path

        if repository_url:
            self.repo = clone_repository(
                repository_url, repository_path, branch=branch)
            remote = self.repo.remote()
            remote.set_url(repository_url)
        elif repository_path:
            self.repo = Repo(repository_path)
    
    def set_all_files_node_cache(self, table_completion_gpt, exclude_files=[], rexclude_files=[], force_cache=True):
        for file_path in list_files_recursively(self.repository_path, exclude_files=exclude_files, rexclude_files=rexclude_files):
            get_file_nodes(table_completion_gpt=table_completion_gpt, file_path=file_path, force_cache=force_cache)
    
    def get_file_node_cache(self, table_completion_gpt, file_path, exclude_files=[], rexclude_files=[]):
        get_file_nodes(table_completion_gpt=table_completion_gpt, file_path=file_path)
