# coding=utf-8
import pytest

from emft.core.downloader import Downloader, get_hash
from emft.core.path import create_temp_file

SMALL = r'http://download.thinkbroadband.com/1MB.zip'
NOPE = r'http://download.thinkbroadband.com/nope.zip'


def test_downloader(tmpdir, mocker):
    mock = mocker.MagicMock()

    dest = create_temp_file(create_in_dir=str(tmpdir))
    success = Downloader(SMALL, dest, hexdigest='f00be31bb73fe783209497d80aa1de89', progress_hooks=[mock]).download()
    assert get_hash(dest.bytes()) == 'f00be31bb73fe783209497d80aa1de89'
    assert success is True
    assert dest.exists()

    assert mock.call_count >= 1

    mock.assert_called_with(
        {'total': 1048576, 'percent_complete': '100.0', 'status': 'finished', 'time': '00:00', 'downloaded': 1048576}
    )


def test_dest_delete(tmpdir):
    dest = create_temp_file(create_in_dir=str(tmpdir))
    assert dest.exists()
    success = Downloader(SMALL, dest, hexdigest='wrong_digest').download()
    assert success is False
    assert not dest.exists()


def test_hook_exception(tmpdir):
    # Checks that Exception in callback does *not* propagate

    def callback():
        raise Exception('yo mamma')

    dest = create_temp_file(create_in_dir=str(tmpdir))
    Downloader(SMALL, dest, hexdigest='wrong_digest', progress_hooks=[callback]).download()


@pytest.mark.parametrize('callback', [set(), 1, 'text', True, dict()])
def test_wrong_hook_param(tmpdir, callback):
    dest = create_temp_file(create_in_dir=str(tmpdir))
    with pytest.raises(TypeError):
        Downloader(SMALL, dest, hexdigest='wrong_digest', progress_hooks=callback).download()


def test_wrong_url(tmpdir):
    dest = create_temp_file(create_in_dir=str(tmpdir))
    success = Downloader(NOPE, dest, hexdigest='wrong_digest').download()
    assert not success
