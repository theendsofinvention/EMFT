from ..value import RemoteGHRepo, RemoteAVRepo, AVProbeResult


class RemoteManager:
    def __init__(self,):
        self._gh_repo = None
        self._av_repo = None

    def set_gh_repo(self, repo_owner: str, repo_name: str):
        self._gh_repo = RemoteGHRepo(
            repo_owner=repo_owner,
            repo_name=repo_name
        )

    def set_av_repo(self, repo_owner: str, repo_name: str):
        self._av_repo = RemoteAVRepo(
            repo_owner=repo_owner,
            repo_name=repo_name
        )
