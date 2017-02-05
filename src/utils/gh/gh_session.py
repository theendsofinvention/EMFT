# coding=utf-8

from ..custom_logging import make_logger
from ..singleton import Singleton
from .gh_anon import GHAnonymousSession
from .gh_errors import GHSessionError
from .gh_objects.gh_mail import GHMail, GHMailList
from .gh_objects.gh_repo import GHRepoList, GHRepo
from .gh_objects.gh_user import GHUser

logger = make_logger(__name__)


# TODO: https://github.com/github/choosealicense.com/tree/gh-pages/_licenses
# TODO https://developer.github.com/v3/licenses/


class GHSession(GHAnonymousSession, metaclass=Singleton):
    session_status = dict(
        not_connected=0,
        connected=1,
        wrong_token=-1,
    )

    def __init__(self, token=None):
        GHAnonymousSession.__init__(self)
        self.gh_user = None
        self.user = None

        if token is None:

            logger.debug('no token given, trying local environment')

            import os
            token = os.environ.get('GH_TOKEN', None)

        self.authenticate(token)

        if self.user is False:
            logger.error('Token was invalidated; please create a new one')
        elif self.user is None:
            logger.info('No user')
        else:
            logger.info('authenticated as: {}'.format(self.user))

    @property
    def has_valid_token(self):
        return isinstance(self.user, str)

    def authenticate(self, token):
        if token is None:
            logger.debug('no token, staying anonymous')
            self.user = None
        else:
            self.headers.update(
                {
                    'Authorization': 'token {}'.format(token)
                }
            )
            self.build_req('user')
            try:
                self.gh_user = GHUser(self._get_json())
                self.user = self.gh_user.login
            except GHSessionError:
                self.user = False
        return self

    def check_authentication(self, _raise=True):
        if not isinstance(self.user, str):
            if _raise:
                raise GHSessionError('unauthenticated')
            return False

    @property
    def rate_limit(self):
        self.build_req('rate_limit')
        req = self._get()
        return req.json().get('resources', {}).get('core', {}).get('remaining', 0)

    @property
    def email_addresses(self) -> GHMailList:
        self.build_req('user', 'emails')
        return GHMailList(self._get_json())

    @property
    def primary_email(self) -> GHMail or None:
        for mail in self.email_addresses:
            assert isinstance(mail, GHMail)
            if mail.primary and mail.verified:
                return mail
        return None

    def create_repo(self,
                    name: str,
                    description: str = None,
                    homepage: str = None,
                    auto_init: bool = False,
                    # license_template: str = None
                    ):
        self.build_req('user', 'repos')
        json = dict(
            name=name,
            description=description,
            homepage=homepage,
            auto_init=auto_init
        )
        self._post(json=json)

    def edit_repo(self,
                  user, repo,
                  new_name: str = None,
                  description: str = None,
                  homepage: str = None,
                  auto_init: bool = False,
                  # license_template: str = None  # TODO GH licenses
                  ):
        if new_name is None:
            new_name = repo
        self.build_req('repos', user, repo)
        json = dict(name=new_name)
        if description:
            json['body'] = description
        if homepage:
            json['homepage'] = homepage
        if auto_init:
            json['auto_init'] = auto_init
        return self._patch(json=json)

    def delete_repo(self, name: str):
        self.check_authentication()
        self.build_req('repos', self.user, name)
        self._delete()

    def list_own_repos(self):
        self.build_req('user', 'repos')
        return GHRepoList(self._get_json())

    def get_repo(self, repo_name: str, user: str = None, **_):
        if user is None:
            self.check_authentication()
            user = self.user
        self.build_req('repos', user, repo_name)
        try:
            return GHRepo(self._get_json())
        except GHSessionError as e:
            if e.msg.startswith('404'):
                raise FileNotFoundError('repository does not exist')

    def create_pull_request(
            self,
            title: str,
            user, repo,
            description: str = None,
            head: str = None, base: str = 'master'):
        self.check_authentication()
        if head is None:
            head = '{}:master'.format(self.user)
        json = dict(
            title=title,
            head=head,
            base=base
        )
        if description:
            json['body'] = description
        self.build_req('repos', user, repo, 'pulls')
        self._post(json=json)

    # FIXME this is just for the lulz
    def create_status(
            self,
            repo: str,
            sha: str,
            state: str,
            target_url: str = None,
            description: str = None,
            context: str = None):
        self.check_authentication()
        self.build_req('repos', self.user, repo, 'statuses', sha)
        json = dict(state=state)
        if target_url:
            json['target_url'] = target_url
        if description:
            json['description'] = description
        if context:
            json['context'] = context
        self._post(json=json)
