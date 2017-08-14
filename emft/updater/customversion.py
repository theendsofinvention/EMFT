# coding=utf-8
from semantic_version import Version as SemanticVersion


class CustomVersion(SemanticVersion):
    """
    Proxy class over semantic_version.Version
    """
    def __init__(self, version_string, partial=False):
        SemanticVersion.__init__(self, version_string, partial)

    # noinspection PyMethodMayBeStatic
    def to_spec(self) -> str:
        return f'{self.major}.{self.minor}.{self.patch}'

    def to_short_string(self) -> str:
        base = f'{self.major}' \
               f'.' \
               f'{self.minor}' \
               f'.' \
               f'{self.patch}'
        if self.prerelease:
            return base + '-' + '.'.join(self.prerelease)
        else:
            return base

    def __repr__(self):
        return super(CustomVersion, self).__repr__().replace('Version(', 'CustomVersion(')
