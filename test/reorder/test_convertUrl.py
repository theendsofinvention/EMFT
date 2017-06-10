import pytest

from src.reorder.service.convert_url import ConvertUrl


class TestConvertUrl:
    @pytest.mark.parametrize(
        'url, repo_owner, repo_name',
        [
            (r'https://github.com/132nd-etcher/EMFT', '132nd-etcher', 'EMFT'),
            (r'git@github.com:132nd-etcher/EMFT.git', '132nd-etcher', 'EMFT'),
            (r'https://github.com/132nd-etcher/EMFT.git', '132nd-etcher', 'EMFT'),
            (
                    r'https://github.com/132nd-vWing/132nd-Virtual-Wing-Training-Mission-Tblisi/issues/37',
                    '132nd-vWing',
                    '132nd-Virtual-Wing-Training-Mission-Tblisi'
            ),
        ]
    )
    def test_convert_gh_url(self, url, repo_owner, repo_name):
        result = ConvertUrl.convert_gh_url(url)
        assert result == (repo_owner, repo_name)

    @pytest.mark.parametrize(
        'url, repo_owner, repo_name',
        [
            (r'https://ci.appveyor.com/project/132nd-etcher/emft/build/artifacts', '132nd-etcher', 'emft'),
        ]
    )
    def test_convert_av_url(self, url, repo_owner, repo_name):
        result = ConvertUrl.convert_av_url(url)
        assert result == (repo_owner, repo_name)
