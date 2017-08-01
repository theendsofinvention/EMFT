# coding=utf-8


class GHSessionError(Exception):
    def __init__(self, msg):
        self.msg = msg

        Exception.__init__(self, msg)


class RequestFailedError(GHSessionError):
    """"""


class AuthenticationError(GHSessionError):
    """"""


class RateLimitationError(GHSessionError):
    """"""


class GithubAPIError(GHSessionError):
    """"""


class NotFoundError(GHSessionError):
    """"""
