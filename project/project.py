import git
from git import Repo


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
