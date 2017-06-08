# coding=utf-8

import pytest
from httmock import HTTMock

from src.utils import Path, Downloader
from src.utils.updater import Version, GithubRelease, GHUpdater, AvailableReleases, Channel
from .test_gh import mock_gh_api, GHRelease


class DummyDownloader(Downloader):
    download_return = True
    downloaded = False

    def download(self):
        self.progress_hooks[0]({'time': '00:00', 'downloaded': 100, 'total': 100})
        DummyDownloader.downloaded = True
        return DummyDownloader.download_return


class DummyGHRel(GithubRelease):
    def __init__(self, version_str):
        GithubRelease.__init__(self, GHRelease({'tag_name': '{}'.format(version_str)}))


def dummy_available(ar, list_of_versions):
    for v in list_of_versions:
        ar.add(DummyGHRel(v))


class TestVersion:
    @pytest.mark.parametrize(
        'version_str, channel, branch',
        [
            ('0.0.0+1', 'stable', None),
            ('0.0.0-dev.13', 'dev', None),
            ('0.0.0-alpha.test.15', 'alpha', 'test'),
            ('0.0.0-beta.test.15', 'beta', 'test'),
            ('0.0.0-rc.15', 'rc', None),
        ]
    )
    def test_init(self, version_str, channel, branch):
        version = Version(version_str)
        assert version.channel.channel_name == channel
        assert version.branch == branch
        assert str(version) == version_str

    @pytest.mark.parametrize(
        'version',
        [
            '0.0',
            '0.0.0.0',
            '0+0.0',
            '0.0.1-alpha+test.15',
        ])
    def test_wrong_init(self, version):
        with pytest.raises(ValueError):
            Version(version)

    @pytest.mark.parametrize(
        'ordered_versions',
        [
            [
                '0.0.0-alpha.test.15',
                '0.0.0-beta.test.15',
                '0.0.0-dev.13',
                '0.0.0',
                '0.0.1-alpha.test.15',
                '0.0.1-alpha.test.16',
                '0.0.1',
            ]
        ]
    )
    def test_version_ordering(self, ordered_versions):
        for i in range(len(ordered_versions) - 1):
            assert Version(ordered_versions[i]) < Version(ordered_versions[i + 1])
            assert Version(ordered_versions[i + 1]) > Version(ordered_versions[i])

    @pytest.mark.parametrize(
        'same_version',
        [
            ('0.0.0-alpha.test.15', '0.0.0-alpha.test.15+1'),
            ('0.0.0-dev.1', '0.0.0-dev.1+some-text'),
            ('0.0.1', '0.0.1+15-some-text'),
        ]
    )
    def test_same_version(self, same_version):
        assert Version(same_version[0]) == Version(same_version[1])


class TestAvailableReleases:
    def test_set_item(self):
        ar = AvailableReleases()
        ar.add(DummyGHRel('0.0.1'))
        assert len(ar) == 1, len(ar)

    @pytest.mark.parametrize('value', ['str', 1, True, None, False, 1.234])
    def test_set_item_wrong_value(self, value):
        ar = AvailableReleases()
        with pytest.raises(TypeError):
            ar.add(value)
        assert len(ar) == 0

    @pytest.mark.parametrize(
        'available, channel, results',
        [
            (['0.0.1'], 'stable', ['0.0.1']),
            (['0.0.1'], 'dev', ['0.0.1']),
            (['0.0.1', '0.0.2', '0.0.3'], 'stable', ['0.0.1', '0.0.2', '0.0.3']),
            (
                    [
                        '0.0.1-dev.1', '0.0.1'
                    ], 'stable', ['0.0.1']
            ),
            (
                    [
                        '0.0.3-dev.1', '0.0.2-rc.1', '0.0.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1'
                    ], 'stable', ['0.0.1']
            ),
            (
                    [
                        '0.0.3-dev.1', '0.0.2-rc.1', '0.0.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1'
                    ], 'rc', ['0.0.1', '0.0.2-rc.1']
            ),
            (
                    [
                        '0.0.3-dev.1', '0.0.2-rc.1', '0.0.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1'
                    ], 'dev', ['0.0.1', '0.0.2-rc.1', '0.0.3-dev.1']
            ),
            (
                    [
                        '0.0.3-dev.1', '0.0.2-rc.1', '0.0.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1'
                    ], 'beta', ['0.0.1', '0.0.2-rc.1', '0.0.3-dev.1', '0.0.4-beta.t.1']
            ),
            (
                    [
                        '0.0.3-dev.1', '0.0.2-rc.1', '0.0.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1'
                    ], 'alpha', ['0.0.1', '0.0.2-rc.1', '0.0.3-dev.1', '0.0.4-beta.t.1', '0.0.5-alpha.t.1']),
            (['0.0.2-alpha.t.1', '0.0.2-alpha.tt.1'], 'beta', None),
        ]
    )
    def test_filter_by_channels(self, available, channel, results):
        ar = AvailableReleases()
        dummy_available(ar, available)
        ar = ar.filter_by_channel(channel)
        if results:
            assert ar
            assert len(ar) == len(results)
            assert all([k in ar.keys() for k in results])
        else:
            assert not ar
            assert len(ar) == 0

    @pytest.mark.parametrize(
        'available, channel, branch, results',
        [
            (['0.0.1'], 'stable', '', ['0.0.1']),
            (['0.0.2-alpha.t.1'], 'stable', '', None),
            (['0.0.2-alpha.t.1'], 'alpha', 'tt', None),
            (['0.0.2-alpha.t.1'], 'alpha', 't', ['0.0.2-alpha.t.1']),
            (['0.0.2-alpha.t.1', '0.0.3-alpha.tt.1'], 'alpha', 't', ['0.0.2-alpha.t.1']),
            (['0.0.2-alpha.t.1', '0.0.3-alpha.tt.1'], 'alpha', 'tt', ['0.0.3-alpha.tt.1']),
            (
                    [
                        '0.0.2-alpha.t.1',
                        '0.0.3-alpha.tt.1',
                        '0.0.3-alpha.tt.2',
                        '0.0.3-alpha.tt.3',
                    ], 'alpha', 'tt',
                    [
                        '0.0.3-alpha.tt.1',
                        '0.0.3-alpha.tt.2',
                        '0.0.3-alpha.tt.3',
                    ]
            ),
        ]
    )
    def test_filter_by_branch(self, available, channel, branch, results):
        ar = AvailableReleases()
        ar2 = AvailableReleases()
        dummy_available(ar, available)
        dummy_available(ar2, available)
        ar = ar.filter_by_branch(branch)
        if channel in ['alpha', 'beta']:
            ar2 = ar2.filter_by_branch(Version('0.0.1-{}.{}.1'.format(channel, branch)))
            assert ar.keys() == ar2.keys()
        if results:
            assert ar
            assert len(ar) == len(results), ar
            assert all([k in ar.keys() for k in results])
        else:
            assert not ar
            assert len(ar) == 0

    @pytest.mark.parametrize(
        'available, result',
        [
            (['0.0.1'], '0.0.1'),
            (['0.0.1', '0.0.2', '0.0.4'], '0.0.4'),
            (['0.0.1', '0.0.2', '0.0.4-alpha.t.1'], '0.0.4-alpha.t.1'),
        ]
    )
    def test_get_latest(self, available, result):
        ar = AvailableReleases()
        dummy_available(ar, available)
        latest = ar.get_latest_release()
        if result:
            assert latest.version == Version(result), latest

    def test_get_latest_empty(self):
        ar = AvailableReleases()
        latest = ar.get_latest_release()
        assert not latest

    def test_filter_by_channel_empty(self):
        ar = AvailableReleases()
        assert not ar.filter_by_channel('stable')

    @pytest.mark.parametrize('channel', ['some', 'string', 1, True, None])
    def test_filter_by_channel_wrong_channel(self, channel):
        ar = AvailableReleases()
        with pytest.raises(ValueError):
            ar.filter_by_channel(channel)


class TestUpdater:
    @pytest.fixture(scope='function')
    def upd(self, mocker):
        cancel = mocker.MagicMock()
        no_new_version = mocker.MagicMock()
        no_candidate = mocker.MagicMock()
        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )
        yield upd, cancel, no_new_version, no_candidate

    @pytest.fixture(scope='function', autouse=True)
    def reset_downloader(self):
        DummyDownloader.downloaded = False
        DummyDownloader.download_return = True
        yield

    @pytest.fixture(scope='function', autouse=True)
    def delete_temp_files(self):
        Path('./update.bat').remove_p()
        Path('./update.vbs').remove_p()
        Path('./update').remove_p()
        yield
        Path('./update.bat').remove_p()
        Path('./update.bat').remove_p()
        Path('./update').remove_p()

    def test_gather_all_available_releases(self, upd: GHUpdater):
        upd, *_ = upd
        assert upd._available == {}

        with HTTMock(mock_gh_api):
            assert upd._gather_available_releases()
            assert len(upd._available) is 7

        upd._gh_repo = 'no_release'

        with HTTMock(mock_gh_api):
            assert not upd._gather_available_releases()
            assert len(upd._available) is 0

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    @pytest.mark.parametrize(
        'current, channel, expected_result',
        [
            ('0.0.1', 'stable', True),
            ('0.0.2', 'stable', False),
            ('0.0.2', 'dev', True),
            ('0.0.3', 'dev', False),
            ('0.0.3-beta.test.1', 'beta', True),
            ('0.0.4-beta.test.1', 'beta', False),
            ('0.0.4-alpha.test.1', 'alpha', True),
            ('0.0.6-alpha.test.1', 'alpha', False),
        ]
    )
    def test_check_version(self, current, channel, expected_result, mocker, upd):
        upd, cancel, no_new_version, no_candidate = upd

        installer = mocker.MagicMock(return_value=True)

        upd._download_and_install_release = installer

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)

        with HTTMock(mock_gh_api):

            result = upd._find_and_install_latest_release(
                channel=channel,
                branch=Version(current).branch,
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                current_version=current,
                executable_path='dummy',
            )
            cancel.assert_not_called()
            no_candidate.assert_not_called()

            if expected_result:
                assert result
                assert upd._available, upd._available
                no_new_version.assert_not_called()
            else:
                assert not result
                no_new_version.assert_called_with()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_no_asset(self, mocker):

        cancel = mocker.MagicMock()
        no_candidate = mocker.MagicMock()
        no_new_version = mocker.MagicMock()

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='no_asset',
        )

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                current_version='0.0.1',
                executable_path='dummy',
            )

            cancel.assert_called_once_with()
            no_new_version.assert_not_called()
            no_candidate.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_download_fail(self, mocker, upd):
        upd, cancel, no_new_version, no_candidate = upd

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)

        DummyDownloader.download_return = False

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                current_version='0.0.1',
                executable_path='dummy',
            )
            assert upd._available, upd._available
            assert DummyDownloader.downloaded is True
            cancel.assert_called_once_with()

        DummyDownloader.download_return = True

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_missing_file(self, mocker, upd):
        upd, cancel, no_new_version, no_candidate = upd

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                current_version='0.0.1',
                executable_path='t'
            )
            assert upd._available, upd._available
            assert DummyDownloader.downloaded is True
            cancel.assert_called_once_with()
            no_candidate.assert_not_called()
            no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_pre_update_hook(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        installer = mocker.MagicMock()

        tmpdir.join('example.zip').write('dummy')

        upd._download_and_install_release = installer

        with HTTMock(mock_gh_api):
            pre = mocker.MagicMock(return_value=False)

            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                pre_update_hook=pre,
                executable_path=Path(str(tmpdir.join('example.zip'))),
                current_version='0.0.1'
            )

            assert upd._available, upd._available
            cancel.assert_called_once_with()
            no_candidate.assert_not_called()
            no_new_version.assert_not_called()
            pre.assert_called_once_with()
            installer.assert_not_called()

            pre = mocker.MagicMock(return_value=True)

            assert upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                pre_update_hook=pre,
                executable_path=Path(str(tmpdir.join('example.zip'))),
                current_version='0.0.1'
            )

            assert upd._available, upd._available
            cancel.assert_called_once_with()
            pre.assert_called_once_with()
            assert installer.call_count == 1
            no_candidate.assert_not_called()
            no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        cancel = mocker.MagicMock()

        tmpdir.join('example.zip').write('dummy')

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=Path(str(tmpdir.join('example.zip'))),
                current_version='0.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is True
        cancel.assert_not_called()
        no_candidate.assert_not_called()
        no_new_version.assert_not_called()
        popen.assert_called_with(['wscript.exe', 'update.vbs', 'update.bat'])
        nice_exit.assert_called_with(0)

        assert Path('./update.bat').exists()
        assert Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_download_fail(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        tmpdir.join('example.zip').write('dummy')

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        DummyDownloader.download_return = False

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=Path(str(tmpdir.join('example.zip'))),
                current_version='0.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is True
        cancel.assert_called_with()
        popen.assert_not_called()
        nice_exit.assert_not_called()
        no_candidate.assert_not_called()
        no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_install_fail(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd
        install = mocker.MagicMock(return_value=False)

        tmpdir.join('example.zip').write('dummy')

        upd._install_update = install

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        exe_path = Path(str(tmpdir.join('example.zip')))

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                executable_path=exe_path,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                current_version='0.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is True
        cancel.assert_called_with()
        popen.assert_not_called()
        nice_exit.assert_not_called()
        install.assert_called_with(exe_path)
        no_candidate.assert_not_called()
        no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_no_new_version(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        tmpdir.join('example.zip').write('dummy')

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=Path(str(tmpdir.join('example.zip'))),
                current_version='9999.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is False
        cancel.assert_not_called()
        popen.assert_not_called()
        nice_exit.assert_not_called()
        no_candidate.assert_not_called()
        no_new_version.assert_called_with()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_exe_path_as_string(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        tmpdir.join('example.zip').write('dummy')

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=str(tmpdir.join('example.zip')),
                current_version='0.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is True
        cancel.assert_not_called()
        popen.assert_called_with(['wscript.exe', 'update.vbs', 'update.bat'])
        nice_exit.assert_called_with(0)
        no_candidate.assert_not_called()
        no_new_version.assert_not_called()

        assert Path('./update.bat').exists()
        assert Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_no_candidates(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        tmpdir.join('example.zip').write('dummy')

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='no_release',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=str(tmpdir.join('example.zip')),
                current_version='0.0.1',
            )

        assert not upd._available, upd._available
        assert DummyDownloader.downloaded is False
        cancel.assert_not_called()
        popen.assert_not_called()
        nice_exit.assert_not_called()
        no_candidate.assert_called_once_with()
        no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_no_asset(self, mocker, tmpdir, upd):
        upd, cancel, no_new_version, no_candidate = upd

        tmpdir.join('example.zip').write('dummy')

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='no_asset',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                cancel_update_hook=cancel,
                no_candidates_hook=no_candidate,
                no_new_version_hook=no_new_version,
                executable_path=str(tmpdir.join('example.zip')),
                current_version='0.0.1',
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is False
        cancel.assert_called_once_with()
        popen.assert_not_called()
        nice_exit.assert_not_called()
        no_candidate.assert_not_called()
        no_new_version.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_install_no_cancel_func(self, mocker, tmpdir):

        tmpdir.join('example.zip').write('dummy')

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='no_asset',
        )

        mocker.patch('src.utils.updater.Downloader', new=DummyDownloader)
        popen = mocker.patch('src.utils.updater.subprocess.Popen')
        nice_exit = mocker.patch('src.utils.updater.nice_exit')

        with HTTMock(mock_gh_api):
            assert not upd._find_and_install_latest_release(
                channel='stable',
                executable_path=str(tmpdir.join('example.zip')),
                current_version='0.0.1'
            )

        assert upd._available, upd._available
        assert DummyDownloader.downloaded is False
        popen.assert_not_called()
        nice_exit.assert_not_called()

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    def test_get_latest_release_from_gh(self):

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )

        with HTTMock(mock_gh_api):
            latest = upd._get_latest_release('stable')

            assert latest.version.version_str == '0.0.2', latest.version.version_str

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()

    @pytest.mark.parametrize(
        'available, channel, branch, result',
        [
            (
                    {'0.0.1', '0.0.2', '0.0.3-dev.1'},
                    'stable', None, '0.0.2',
            ),
            (
                    {'0.0.1', '0.0.2', '0.0.3-dev.1'},
                    'dev', None, '0.0.3-dev.1',
            ),
            (
                    {'0.0.1', '0.0.2-rc.3', '0.0.3-dev.1'},
                    'rc', None, '0.0.2-rc.3',
            ),
            (
                    {'0.0.1', '0.0.2', '0.0.3-dev.1', '0.0.4-beta.test.1'},
                    'dev', None, '0.0.3-dev.1',
            ),
            (
                    {'0.0.4-beta.test.1', '0.0.4-alpha.test.1'},
                    'beta', 'test', '0.0.4-beta.test.1',
            ),
            (
                    {'0.0.4-beta.test.1', '0.0.4-alpha.test.1'},
                    'alpha', 'test', '0.0.4-beta.test.1',
            ),
            (
                    {'0.0.4-beta.test.1', '0.0.5-alpha.test.1'},
                    'alpha', 'test', '0.0.5-alpha.test.1',
            ),
            (
                    {'0.0.4-beta.test.1', '0.0.5-beta.other.1'},
                    'beta', 'test', '0.0.4-beta.test.1',
            ),
        ]
    )
    def test_get_latest_release(self, available, channel, branch, result, mocker):

        gather_available = mocker.MagicMock()

        upd = GHUpdater(
            gh_user='132nd-etcher',
            gh_repo='EASI',
        )

        upd._gather_available_releases = gather_available

        dummy_available(upd._available, available)

        with HTTMock(mock_gh_api):
            latest = upd._get_latest_release(channel, branch)

            assert latest.version.version_str == result, latest.version.version_str

        assert not Path('./update.bat').exists()
        assert not Path('./update.vbs').exists()
        assert not Path('./update').exists()


class TestGHRelease:
    @pytest.mark.parametrize(
        'gh_release',
        [
            ({"tag_name": "0.0.1"}, '0.0.1', 'stable', None),
            ({"tag_name": "0.0.2-alpha.test.1"}, '0.0.2-alpha.test.1', 'alpha', 'test'),
            ({"tag_name": "0.0.2-beta.test.1+532"}, '0.0.2-beta.test.1', 'beta', 'test'),
            ({"tag_name": "0.0.3-rc.1"}, '0.0.3-rc.1', 'rc', None),
        ]
    )
    def test_gh_release(self, gh_release):
        json, version_str, channel, branch = gh_release

        gh_rel = GithubRelease(GHRelease(json))
        assert gh_rel.version == Version(version_str)
        assert gh_rel.channel == Channel(channel)
        assert gh_rel.branch == branch

        # @pytest.mark.parametrize(
        #     'gh_assets',
        #     [
        #         (
        #                 {"tag_name": "0.0.1",
        #                  "assets":
        #                      [
        #                          {"browser_download_url": "the_url", "name": "example.zip"},
        #                      ]
        #                  },
        #                 'example.zip', 'the_url'
        #         ),
        #         (
        #                 {"tag_name": "0.0.1",
        #                  "assets":
        #                      [
        #                          {"browser_download_url": "the_url1", "name": "EXAMPLE1"},
        #                          {"browser_download_url": "the_url2", "name": "EXAMPLE2"},
        #                          {"browser_download_url": "the_url3", "name": "EXAMPLE3"},
        #                          {"browser_download_url": "the_url4", "name": "EXAMPLE4"},
        #                      ]
        #                  },
        #                 'example3', 'the_url3'
        #         ),
        #     ]
        # )
        # def test_gh_release_assets(self, gh_assets):
        #     json, asset_name, dld_url = gh_assets
        #     gh_rel = GithubRelease(GHRelease(json))
        #     assert gh_rel.get_asset_download_url('some_asset') is None
        #     assert gh_rel.get_asset_download_url(asset_name) == dld_url
