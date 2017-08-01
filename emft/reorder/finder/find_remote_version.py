# coding=utf-8

from emft.reorder.value import RemoteVersion, AVProbeResult


class FindRemoteVersion:
    @staticmethod
    def get_latest() -> AVProbeResult:
        return RemoteVersion.LATEST_REMOTE_VERSION
