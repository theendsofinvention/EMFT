# coding=utf-8
import requests

from .gh_errors import GithubAPIError, RateLimitationError, AuthenticationError, GHSessionError, \
    RequestFailedError, NotFoundError
from .gh_objects.gh_asset import GHAllAssets, GHAsset
from .gh_objects.gh_authorization import GHAuthorization
from .gh_objects.gh_ref import GHRef
from .gh_objects.gh_release import GHRelease, GHAllReleases
from .gh_objects.gh_repo import GHRepoList, GHRepo
from .gh_objects.gh_user import GHUser
from ..custom_logging import make_logger
from ..singleton import Singleton

logger = make_logger(__name__)


class GHAnonymousSession(requests.Session, metaclass=Singleton):
    def __init__(self):

        requests.Session.__init__(self)

        self.base = ['https://api.github.com']

        self.__resp = None

        self.req = None

    @property
    def resp(self) -> requests.models.Response:
        return self.__resp

    def build_req(self, *args):

        if not args:
            raise ValueError('request is empty')

        for x in args:
            if not isinstance(x, str):
                raise TypeError('expected a string, got: {} ({})'.format(x, args))

        self.req = '/'.join(self.base + list(args))

        return self.req

    def __parse_resp_error(self):

        logger.error(self.req)

        if self.resp.status_code >= 500:
            raise GithubAPIError(r'Github API seems to be down, check https://status.github.com/')

        else:

            code = self.resp.status_code

            reason = self.resp.reason

            msg = [str(code), reason]

            json = self.resp.json()

            if json:
                msg.append('GH_MSG: {}'.format(json.get('message')))
                msg.append('GH_DOC: {}'.format(json.get('documentation_url')))

                if code == 403 and json.get('message').startswith('API rate limit exceeded for '):
                    raise RateLimitationError(': '.join(msg))

            if code == 401:
                raise AuthenticationError(': '.join(msg))

            elif code == 404:
                raise NotFoundError(self.req)

            else:
                raise GHSessionError(': '.join(msg))

    def __parse_resp(self) -> requests.models.Response:

        if self.__resp is None:
            raise RequestFailedError('did not get any response from: {}'.format(self.req))

        if not self.__resp.ok:
            self.__parse_resp_error()

        logger.debug(self.__resp.reason)

        return self.__resp

    def _get(self, **kwargs) -> requests.models.Response:

        logger.debug(self.req)

        self.__resp = super(GHAnonymousSession, self).get(self.req, **kwargs)

        return self.__parse_resp()

    def _put(self, **kwargs) -> requests.models.Response:

        logger.debug(self.req)

        self.__resp = super(GHAnonymousSession, self).put(self.req, **kwargs)

        return self.__parse_resp()

    def _get_json(self, **kwargs) -> requests.models.Response:

        req = self._get(**kwargs)

        return req.json()

    def _post(self, data=None, json: dict = None, **kwargs) -> requests.models.Response:

        logger.debug(self.req)

        self.__resp = super(GHAnonymousSession, self).post(self.req, data, json, **kwargs)

        return self.__parse_resp()

    def _patch(self, data=None, **kwargs) -> requests.models.Response:

        logger.debug(self.req)

        self.__resp = super(GHAnonymousSession, self).patch(self.req, data, **kwargs)

        return self.__parse_resp()

    def _delete(self, **kwargs) -> requests.models.Response:

        logger.debug(self.req)

        self.__resp = super(GHAnonymousSession, self).delete(self.req, **kwargs)

        return self.__parse_resp()

    def get_latest_release(self, user: str, repo: str) -> GHRelease:

        self.build_req('repos', user, repo, 'releases', 'latest')

        return GHRelease(self._get_json())

    def get_all_releases(self, user: str, repo: str):

        self.build_req('repos', user, repo, 'releases')

        return GHAllReleases(self._get_json())

    def get_all_assets(self, user: str, repo: str, release_id: int):

        self.build_req('repos', user, repo, 'releases', str(release_id), 'assets')

        return GHAllAssets(self._get_json())

    def get_asset(self, user: str, repo: str, release_id: int, asset_id: int):

        self.build_req('repos', user, repo, 'releases', str(release_id), 'assets', str(asset_id))

        return GHAsset(self._get_json())

    def list_user_repos(self, user: str) -> GHRepoList:

        self.build_req('users', user, 'repos')

        return GHRepoList(self._get_json())

    def get_repo(self, user: str, repo: str) -> GHRepo:

        self.build_req('repos', user, repo)

        return GHRepo(self._get_json())

    def get_user(self, user: str) -> GHUser:

        self.build_req('users', user)

        return GHUser(self._get_json())

    def get_ref(self, user: str, repo: str, branch: str) -> GHRef:

        self.build_req('repos', user, repo, 'git', 'refs', 'heads', branch)

        return GHRef(self._get_json())

    def list_authorizations(self, username, password) -> list:

        auth_list = []

        def __add_auth(json):
            nonlocal auth_list
            for x in json:
                auth_list.append(GHAuthorization(x))

        self.build_req('authorizations')

        req = self._get(auth=(username, password))

        __add_auth(req.json())

        while 'next' in req.links:
            req = self.get(req.links['next']['url'], auth=(username, password))
            __add_auth(req.json())

        return auth_list

    def remove_authorization(self, username, password, auth_id):

        self.build_req('authorizations', str(auth_id))

        self._delete(auth=(username, password))
