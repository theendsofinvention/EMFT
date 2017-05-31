import requests
from utils import make_logger
from src.misc.github.value.branch import Branch, BranchesArray
from src.sentry import SENTRY

logger = make_logger(__name__)


class GHProbe:
    def __init__(self, repo_owner: str, repo_name: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self._branches = BranchesArray()

    @property
    def branches(self) -> BranchesArray:
        return self._branches

    def get_available_branches(self):
        req = requests.get(
            f'https://api.github.com/'
            f'repos/'
            f'{self.repo_owner}/'
            f'{self.repo_name}/'
            f'branches')

        if not req.ok:
            error = f'request failed: {req.url}\nreason: {req.reason}\ntext: {req.text}'
            logger.error(error)
            SENTRY.captureMessage(error)
            self._branches = BranchesArray()

        else:
            self._branches = BranchesArray([Branch(b['name']) for b in req.json()])

        return self
