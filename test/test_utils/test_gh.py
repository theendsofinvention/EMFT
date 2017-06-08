# coding=utf-8

import os
from json import loads, dumps

import pytest
import requests
from httmock import response, urlmatch, with_httmock

from src.utils.custom_path import Path
from src.utils.gh import GHAnonymousSession, GHSessionError, NotFoundError, RateLimitationError, GithubAPIError, \
    GHAllAssets, GHRelease, GHRepo, GHRepoList, GHUser, GHSession, GHAuthorization, GHApp, GHPermissions, GHMailList, \
    GHMail
from src.utils.singleton import Singleton


def test_build_req():
    s = GHAnonymousSession()
    assert s.build_req('test', 'test') == 'https://api.github.com/test/test'
    with pytest.raises(ValueError):
        s.build_req()
    with pytest.raises(TypeError):
        s.build_req(1)


ENDPOINT = r'(.*\.)?api\.github\.com$'
HEADERS = {'content-type': 'application/json'}
GET = 'get'
PATCH = 'patch'


class GHResource:
    def __init__(self, path):
        self.path = path

    def get(self):
        return Path(self.path).text()

    def patch(self, request):
        req_j = request.body.decode()
        req_d = loads(req_j)
        local_j = Path(self.path).text()
        local_d = loads(local_j)
        assert isinstance(local_d, dict)
        local_d.update(req_d)
        local_j = dumps(local_d)
        return response(200, local_j, HEADERS, 'OK', 5, request)


current_user = 'octocat'


def check_fail(url, request):
    if url.path.endswith('le_resp_is_empty'):
        return None
    if url.path.endswith('le_api_is_down'):
        return response(500, None, HEADERS, 'Error', 5, request)
    if url.path.endswith('le_rate_is_exceeded'):
        return response(403, {'message': 'API rate limit exceeded for '}, HEADERS, 'Error', 5, request)
    if url.path.endswith('le_random_error'):
        return response(402, {'message': 'Random message'}, HEADERS, 'Error', 5, request)
    return 'ok'


def get_file_path(url):
    if '/user/' in url.path:
        file_path = url.netloc + url.path.replace('/user/', '/user/{}/'.format(current_user)) + '.json'
    else:
        file_path = url.netloc + url.path + '.json'
    if not os.path.exists(file_path):
        file_path = 'test/test_utils/{}'.format(file_path)
    if not os.path.exists(file_path):
        return False
    return file_path


@urlmatch(netloc=ENDPOINT)
def mock_gh_api(url, request):
    assert isinstance(request, requests.models.PreparedRequest)
    fail = check_fail(url, request)
    if not fail == 'ok':
        return fail
    if fail is None:
        return None
    file_path = get_file_path(url)
    try:
        if request.method == 'GET':
            content = GHResource(file_path).get()
        elif request.method == 'PATCH':
            content = GHResource(file_path).patch(request)
        else:
            raise ValueError('request not handled: {}'.format(request.method))
    except EnvironmentError:
        return response(404, {}, HEADERS, 'FileNotFound: {}'.format(file_path), 5, request)
    return response(200, content, HEADERS, 'Success', 5, request)


@pytest.mark.skipif(os.path.exists('./tests/api.github.com'), reason='No test files')
class TestGH:
    @with_httmock(mock_gh_api)
    def test_api_down(self):
        with pytest.raises(GithubAPIError):
            GHAnonymousSession().get_user('le_api_is_down')

    @with_httmock(mock_gh_api)
    def test_rate_exceeded(self):
        with pytest.raises(RateLimitationError):
            GHAnonymousSession().get_user('le_rate_is_exceeded')

    @with_httmock(mock_gh_api)
    def test_other_error(self):
        with pytest.raises(GHSessionError):
            GHAnonymousSession().get_user('le_random_error')

    @with_httmock(mock_gh_api)
    def test_request_failed(self):
        with pytest.raises(NotFoundError):
            GHAnonymousSession().get_user('le_resp_is_empty')

    @with_httmock(mock_gh_api)
    def test_get_repo(self):
        repo = GHAnonymousSession().get_repo('octocat', 'ze_repo')

        assert repo is not None
        assert isinstance(repo, GHRepo)
        assert repo.name == 'Hello-World'

        perms = repo.permissions()
        assert isinstance(perms, GHPermissions)
        assert perms.admin is False
        assert perms.pull is True
        assert perms.push is False

        owner = repo.owner()
        assert isinstance(owner, GHUser)
        assert owner.id == 1
        assert owner.login == 'octocat'

        source = repo.source()
        assert isinstance(source, GHRepo)
        assert source.name == 'Hello-World'

    @with_httmock(mock_gh_api)
    def test_get_user(self):
        user = GHAnonymousSession().get_user('octocat')

        assert user.login == 'octocat'
        assert user.email == 'octocat@github.com'

    @with_httmock(mock_gh_api)
    def test_primary_email(self):
        global current_user
        current_user = 'octocat'
        mail = GHSession().primary_email
        assert mail.email == 'octocat@github.com'
        current_user = 'octodog'
        mail = GHSession().primary_email
        assert mail is None
        current_user = 'octocub'
        mail = GHSession().primary_email
        assert mail is None
        current_user = 'octocat'

    @with_httmock(mock_gh_api)
    def test_get_repos(self):
        global current_user
        current_user = 'octocat'
        repos = GHSession().list_own_repos()
        assert len(repos) == 1
        r = repos['Hello-World']
        assert r.name == 'Hello-World'
        assert r.full_name == 'octocat/Hello-World'

        with pytest.raises(FileNotFoundError):
            _ = GHSession().get_repo('nope', 'octocat')

    @with_httmock(mock_gh_api)
    def test_edit_repo(self, mocker):
        s = GHSession()
        s.gh_user = mocker.MagicMock(login='octocat')
        s.user = 'octocat'
        repo = s.get_repo('ze_repo')
        assert repo.name == 'Hello-World'
        resp = GHSession().edit_repo('octocat', 'ze_repo', new_name='ze_other_repo')
        assert isinstance(resp, requests.models.Response)
        assert resp.status_code == 200
        repo = s.get_repo('ze_repo')
        d = loads(resp.content.content.decode())
        for k in d.keys():
            if k == 'name':
                assert d[k] == 'ze_other_repo'
            else:
                try:
                    x = getattr(repo, k)
                    if callable(x):
                        continue
                    assert d[k] == x
                except AttributeError:
                    pass

    @with_httmock(mock_gh_api)
    def test_list_own_repos(self, mocker):
        s = GHSession()
        s.user = mocker.MagicMock(login='octocat')
        repos = s.list_own_repos()
        assert len(repos) == 1
        assert 'Hello-World' in repos

    @with_httmock(mock_gh_api)
    def test_releases(self):
        releases = GHAnonymousSession().get_all_releases('132nd-etcher', 'EASI')
        assert len(releases) == 7
        assert len(list(releases.final_only())) == 1
        assert len(list(releases.prerelease_only())) == 6
        assert isinstance(releases['rel1'], GHRelease)
        assert isinstance(releases['rel2'], GHRelease)
        assert 'rel1' in releases
        with pytest.raises(AttributeError):
            _ = releases['rel3']
        assert ('rel3' in releases) is False

    @with_httmock(mock_gh_api)
    def test_get_latest_release(self):
        latest = GHAnonymousSession().get_latest_release('132nd-etcher', 'EASI')
        assert latest.assets_url == 'https://api.github.com/repos/octocat/Hello-World/releases/1/assets'
        assert isinstance(latest.assets, GHAllAssets)
        assert len(latest.assets) == 1 == latest.assets_count
        assert isinstance(latest.author, GHUser)
        assert latest.body == 'Description of the release'
        assert latest.created_at == '2013-02-27T19:35:32Z'
        assert latest.draft is False
        assert latest.html_url == 'https://github.com/octocat/Hello-World/releases/v1.0.0'
        assert latest.name == 'v1.0.0'
        assert latest.prerelease is False
        assert latest.published_at == '2013-02-27T19:35:32Z'
        assert latest.tag_name == 'v1.0.0'
        assert latest.url == 'https://api.github.com/repos/octocat/Hello-World/releases/1'

    @with_httmock(mock_gh_api)
    def test_gh_asset(self):
        asset = GHAnonymousSession().get_asset('132nd-etcher', 'EASI', 1, 1)
        assert asset.url == 'https://api.github.com/repos/octocat/Hello-World/releases/assets/1'
        assert asset.id == 1
        assert asset.name == 'example.zip'
        assert asset.label == 'short description'
        assert isinstance(asset.uploader(), GHUser)
        assert asset.content_type == 'application/zip'
        assert asset.state == 'uploaded'
        assert asset.size == 1024
        assert asset.download_count == 42
        assert asset.created_at == '2013-02-27T19:35:32Z'
        assert asset.updated_at == '2013-02-27T19:35:32Z'
        assert asset.browser_download_url == 'https://github.com/octocat/Hello-World/releases/download/v1.0.0/example.zip'

    @with_httmock(mock_gh_api)
    def test_get_all_asset(self):
        all_assets = GHAnonymousSession().get_all_assets('132nd-etcher', 'EASI', 1)
        assert isinstance(all_assets, GHAllAssets)
        assert len(all_assets) == 1

    @with_httmock(mock_gh_api)
    def test_authorization(self):
        Singleton.wipe_instances('GHSession')
        GHSession()
        auth_list = GHSession().list_authorizations(None, None)
        assert len(auth_list) == 1
        auth = auth_list[0]
        assert isinstance(auth, GHAuthorization)
        app = auth.app()
        assert isinstance(app, GHApp)
        assert app.name == 'my github app'
        assert app.url == 'http://my-github-app.com'
        assert app.client_id == 'abcde12345fghij67890'

    @with_httmock(mock_gh_api)
    def test_mail(self):
        Singleton.wipe_instances('GHSession')
        GHSession()
        assert not GHSession().user
        mails = GHSession().email_addresses
        assert isinstance(mails, GHMailList)
        for mail in mails:
            assert isinstance(mail, GHMail)
        assert len(mails) == 2
        assert 'octocat@catsunited.com' in mails
        assert 'octocat@github.com' in mails
        with pytest.raises(AttributeError):
            _ = mails['nope@nil.com']
        assert 'nope@nil.com' not in mails


# noinspection PyPep8Naming
@pytest.mark.skipif(os.getenv('APPVEYOR'), reason='AppVeyor gets 403 from GH all the time')
class TestGHAnonymousSession:

    def test_users_repos(self):
        try:
            repos = GHAnonymousSession().list_user_repos('easitest')
        except RateLimitationError:
            return
        assert isinstance(repos, GHRepoList)
        assert 'unittests' in repos
        assert 'some_repo' not in repos
        repo = repos['unittests']
        assert isinstance(repo, GHRepo)

    def test_latest_release(self):
        try:
            latest = GHAnonymousSession().get_latest_release('132nd-etcher', 'unittests')
        except RateLimitationError:
            return
        assert isinstance(latest, GHRelease)
        assert latest.author.login == '132nd-etcher'
        assert not latest.prerelease
        assert latest.name == 'Final-release 1'
        assert latest.tag_name == '0.0.1.0'
        assert 'README.rst' in latest.assets

    def test_new_gh_session(self, monkeypatch):
        try:
            monkeypatch.delenv('GH_TOKEN')
        except KeyError:
            pass
        Singleton.wipe_instances('GHSession')
        GHSession()
        assert GHSession().user is None

    def test_user(self):
        try:
            usr = GHAnonymousSession().get_user('132nd-etcher')
        except RateLimitationError:
            return
        assert isinstance(usr, GHUser)
        assert usr.id == 21277151
        assert usr.type == 'User'
