# coding=utf-8
from semantic_version import Spec as SemanticSpec

from emft.utils import make_logger
from emft.utils.updater.channel import Channel
from emft.utils.updater.customversion import CustomVersion


LOGGER = make_logger(__name__)


class CustomSpec(SemanticSpec):
    def filter_channel(self, versions, prerelease: str = Channel.stable):
        LOGGER.debug(f'filtering {len(versions)} versions against {self}')
        unknown_pre_release_tags = set()
        for version in super(CustomSpec, self).filter(versions):
            assert isinstance(version, CustomVersion)
            if version.prerelease:
                if not prerelease:
                    if 'prerelease' not in unknown_pre_release_tags:
                        unknown_pre_release_tags.add('prerelease')
                        LOGGER.debug(f'skipping pre-release "{version}"')
                    continue
                if version.prerelease[0] in ('PullRequest',):
                    if 'pull request' not in unknown_pre_release_tags:
                        unknown_pre_release_tags.add('pull request')
                        LOGGER.debug(f'skipping pull-request "{version}"')
                    continue
                if version.prerelease[0] not in Channel.all:
                    if version.prerelease[0] not in unknown_pre_release_tags:
                        unknown_pre_release_tags.add(version.prerelease[0])
                        LOGGER.debug(f'skipping unknown pre-release tag "{version.prerelease[0]}"')
                    continue
                if version.prerelease[0] < prerelease:
                    LOGGER.debug(f'skipping pre-release "{version}" because it is not on channel "{prerelease}"')
                    continue
            yield version

    def select_channel(self, versions, channel: str = Channel.stable):
        LOGGER.debug(f'selecting latest version amongst {len(versions)}')
        options = list(self.filter_channel(versions, channel))
        if options:
            latest = max(options)
            return latest
        LOGGER.debug('no version passed the test')
        return None
