# coding=utf-8

import os
from json import loads, dumps

import pytest
import requests
from httmock import response, urlmatch, HTTMock

from emft.utils import Path
from emft.utils.av import AVSession

ENDPOINT = r'(.*\.)?ci\.appveyor\.com$'
HEADERS = {'content-type': 'application/json'}
GET = 'get'
PATCH = 'patch'

current_user = '132nd-etcher'


class AVResource:
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
        raise FileNotFoundError(os.path.abspath(file_path))
        return False
    return file_path


@urlmatch(netloc=ENDPOINT)
def mock_av_api(url, request):
    assert isinstance(request, requests.models.PreparedRequest)
    fail = check_fail(url, request)
    if not fail == 'ok':
        return fail
    if fail is None:
        return None
    file_path = get_file_path(url)
    try:
        if request.method == 'GET':
            content = AVResource(file_path).get()
        elif request.method == 'PATCH':
            content = AVResource(file_path).patch(request)
        else:
            raise ValueError('request not handled: {}'.format(request.method))
    except EnvironmentError:
        return response(404, {}, HEADERS, 'FileNotFound: {}'.format(file_path), 5, request)
    return response(content=content, headers=HEADERS, reason='Success', elapsed=5, request=request)


def test_build_req():
    s = AVSession()
    assert s.build_req('test', 'test') == r'https://ci.appveyor.com/api/test/test'
    with pytest.raises(ValueError):
        s.build_req()
    with pytest.raises(TypeError):
        s.build_req(1)


@pytest.mark.nocleandir
class TestAVSession:
    @pytest.fixture(autouse=True)
    def mock_av_api(self):
        with HTTMock(mock_av_api):
            yield

    def test_init(self):
        s = AVSession()
        assert s.req is None
        assert s.resp is None

    # @with_httmock(mock_av_api)
    def test_get_last_build(self):
        s = AVSession()
        b1 = s.get_last_build(
            '132nd-etcher',
            'EMFT',
        )
        b2 = s.get_last_build(
            '132nd-etcher',
            'EMFT',
            'master'
        )
        assert b1.build.buildId == b2.build.buildId == 134173
        assert b1.project.name == b2.project.name == 'nuget-test'
        assert b1.project.accountName == b2.project.accountName == 'appvyr'

    def test_get_artifacts(self):
        s = AVSession()
        a = s.get_artifacts('some_build_id')
        assert len(a) == 2
        assert 'emft' in a
        a1 = a['emft']
        assert a1.fileName == 'emft.exe'
        assert a1.type == 'File'
        assert a1.size == 21843754
        a2 = a['hexdigest']
        assert a2.fileName == 'emft.md5'
        assert a2.type == 'File'
        assert a2.size == 43
        a = s.get_artifacts('some_other_build')
        assert len(a) == 1
        a2 = a['hexdigest']
        assert a2.fileName == 'emft.md5'
        assert a2.type == 'File'
        assert a2.size == 43

    def test_get_history(self):
        s = AVSession()
        h = s.get_history('132nd-etcher', 'EMFT')
        p = h.project
        assert p.name == 'EMFT'
        assert p.accountName == '132nd-etcher'
        assert p.accountId == 47829
        assert p.isPrivate is False
        assert p.slug == 'emft'
        assert p.repositoryBranch is None
        assert p.repositoryName == '132nd-etcher/EMFT'
        assert p.repositoryScm == 'git'
        assert p.repositoryType == 'gitHub'
        assert p.created == '2017-02-05T17:00:50.6522765+00:00'
        assert p.updated == '2017-06-08T06:13:18.0515425+00:00'
        assert len(h.builds) == 236
        assert 9161635 in h.builds

    def test_get_latest_build_on_branch(self):
        s = AVSession()
        b = s.get_latest_build_on_branch('132nd-etcher', 'EMFT', 'master')
        assert b.build.buildId == 134173
        assert b.build.jobs[0].jobId == "9r2qufuu8"

    def test_get_build_by_version(self):
        s = AVSession()
        b = s.get_build_by_version('132nd-etcher', 'EMFT', '134173')
        assert b.build.buildId == 134173
        assert b.build.jobs[0].jobId == "9r2qufuu8"
