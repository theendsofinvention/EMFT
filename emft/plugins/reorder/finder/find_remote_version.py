# coding=utf-8

from emft.plugins.reorder.value import AVProbeResult, RemoteVersion


class FindRemoteVersion:
    @staticmethod
    def get_latest() -> AVProbeResult:
        return RemoteVersion.LATEST_REMOTE_VERSION
