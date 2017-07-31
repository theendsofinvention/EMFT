# coding=utf-8

import pytest
import transitions
from httmock import with_httmock

from src.utils.av import AVHistory, AVBuild
from src.utils import make_logger
from src.utils.updater import Updater, CustomVersion, Channel
from test.test_utils.test_av import mock_av_api

DEFAULT_PARAMS = {
    'current_version': '0.1.0',
    'av_user': '132nd-etcher',
    'av_repo': 'EMFT',
    'local_executable': 'emft.exe',
    'channel': Channel.stable,
}

LOGGER = make_logger(__name__)


class DummyAVBuild(AVBuild):
    def __init__(self, version, status, job_id=None):
        AVBuild.__init__(
            self,
            {
                'version': version,
                'status': status,
                'jobs': [
                    {
                        'jobId': job_id
                    }
                ]
            }
        )


class DummyAVHistory(AVHistory):
    # def __init__(self, build_list: typing.List[typing.Tuple[str, typing.Optional[bool]]]):
    def __init__(self, build_list: list):
        builds = []
        for build in build_list:
            assert isinstance(build, dict)
            build['status'] = build.get('status', 'success')
            builds.append(build)
        json = {
            'builds': builds
        }
        AVHistory.__init__(self, json)


def test_init():
    u = Updater(**DEFAULT_PARAMS)
    assert isinstance(u.current_version, CustomVersion)
    assert str(u.current_version) == DEFAULT_PARAMS['current_version']
    assert isinstance(u, transitions.Machine)
    assert u.state == 'initial'
    assert u.latest_version is None
    assert len(u.av_builds) == 0
    assert u.asset is None
    assert u.is_ready is True
    assert u._av_user == DEFAULT_PARAMS['av_user']
    assert u._av_repo == DEFAULT_PARAMS['av_repo']
    assert u._local_executable == DEFAULT_PARAMS['local_executable']
    assert u._hexdigest is None


def test_collection_av_get_history(qtbot, mocker):
    av_session = mocker.patch('src.utils.updater.updater.AVSession', spec=True)
    u = Updater(**DEFAULT_PARAMS)
    assert u.state == 'initial'
    u.look_for_new_version(auto_update=False)
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_with())
    assert mocker.call() in av_session.mock_calls
    assert mocker.call().get_history(DEFAULT_PARAMS['av_user'], DEFAULT_PARAMS['av_repo']) in av_session.mock_calls
    assert mocker.call().get_history().builds.successful_only() in av_session.mock_calls
    assert u._av_builds == dict()
    qtbot.wait_until(lambda: u.state == 'waiting')
    assert u.latest_version is None


def test_collection_reset_values(qtbot, mocker):
    av_session = mocker.patch('src.utils.updater.updater.AVSession', spec=True)
    u = Updater(**DEFAULT_PARAMS)
    assert u.state == 'initial'
    reset_mock = mocker.spy(u, '_reset_internal_values')
    u.look_for_new_version(auto_update=False)
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_with())
    reset_mock.assert_called_once()
    qtbot.wait_until(lambda: u.state == 'waiting')


def test_collection_auto_update_value(qtbot, mocker):
    av_session = mocker.patch('src.utils.updater.updater.AVSession', spec=True)
    u = Updater(**DEFAULT_PARAMS)
    assert u.state == 'initial'
    u.look_for_new_version()
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_with())
    assert u._auto_update is False
    u = Updater(**DEFAULT_PARAMS)
    assert u.state == 'initial'
    u.look_for_new_version(auto_update=False)
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_with())
    assert u._auto_update is False
    u = Updater(**DEFAULT_PARAMS)
    assert u.state == 'initial'
    u.look_for_new_version(auto_update=True)
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_with())
    assert u._auto_update is True
    qtbot.wait_until(lambda: u.state == 'waiting')


def test_finalize_event_error(mocker, caplog):
    def dummy_raise(event):
        assert isinstance(event, transitions.EventData)
        raise ValueError('uh oh!')

    mocker.patch('src.utils.updater.updater.AVSession', spec=True)
    u = Updater(**DEFAULT_PARAMS)
    u.dummy_raise = dummy_raise
    u.add_states('failed')
    u.add_transition('fail', '*', 'failed', after='dummy_raise')
    with pytest.raises(ValueError):
        u.fail()
    assert "from: fail({}): error: <class 'ValueError'>: uh oh!" in caplog.text


def test_finalize_event_no_error(mocker, caplog):
    def dummy_pass(event):
        assert isinstance(event, transitions.EventData)

    mocker.patch('src.utils.updater.updater.AVSession', spec=True)
    u = Updater(**DEFAULT_PARAMS)
    u.dummy_pass = dummy_pass
    u.add_states('passed')
    u.add_transition('pass_', '*', 'passed', after='dummy_pass')
    u.pass_()
    assert "from: pass_({}): done:  state: passed" in caplog.text


@pytest.mark.parametrize(
    'av_builds,expected_keys', [
        (
                (('0.1.0', 'success'), ('0.2.0', 'fail')), ('0.1.0',),
        ),
        (
                (('0.1.0', 'success'), ('0.2.0', 'success')), ('0.1.0', '0.2.0'),
        )])
def test_collection_with_result(av_builds, expected_keys, qtbot, mocker):
    av_session = mocker.patch(
        'src.utils.updater.updater.AVSession.get_history',
        spec=True,
        return_value=DummyAVHistory([dict(version=build[0], status=build[1]) for build in av_builds])
    )
    u = Updater(**DEFAULT_PARAMS)
    parser = mocker.patch.object(u, '_parse_available_releases')
    assert u.state == 'initial'
    qtbot.wait_until(lambda: av_session.assert_not_called())
    u.look_for_new_version(auto_update=False)
    qtbot.wait_until(lambda: u.state == 'collecting')
    qtbot.wait_until(lambda: av_session.assert_called_once())
    qtbot.wait_until(lambda: u.state == 'parsing')
    assert list(map(CustomVersion, expected_keys)) == list(u.av_builds.keys())
    parser.assert_called_once()


@with_httmock(mock_av_api)
@pytest.mark.nocleandir
@pytest.mark.parametrize(
    'channel,expected_version',
    [
        (Channel.stable, '0.4.3'),
        (Channel.patch, '0.4.4-patch.1'),
        (Channel.exp, '0.5.0-exp.3'),
        (Channel.beta, '0.6.0-beta.2'),
        (Channel.alpha, '0.7.0-alpha.3'),
    ]
)
def test_parsing(channel, expected_version, qtbot, mocker, caplog):
    from src.utils.updater.updater import AVSession
    get_build_by_version_mock = mocker.spy(AVSession, 'get_build_by_version')
    u = Updater(DEFAULT_PARAMS['current_version'], 'test', 'test_updater_parser', 'emft.exe', channel)
    reset_mock = mocker.spy(u, '_reset_internal_values')
    parser_mock = mocker.spy(u, '_parse_available_releases')
    assert u.state == 'initial'
    u.look_for_new_version()
    qtbot.wait_until(lambda: u.state == 'waiting')
    reset_mock.assert_called_once()
    parser_mock.assert_called_once()
    get_build_by_version_mock.assert_called_once()
    assert u.latest_version.to_short_string() == expected_version
    if channel == Channel.stable:
        assert 'skipping pre-release' in caplog.text
    else:
        assert 'skipping badly formatted version string: "pending.275"' in caplog.text
        assert 'skipping pull-request "1.5.0-PullRequest.CARIBOU.2+Branch.develop' \
               '.Sha.00f729ecac19ef6fd89a4b865a86907fedd7bf1b.276"' in caplog.text
