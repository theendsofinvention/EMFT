# coding=utf-8
class Channel:
    __slots__ = []
    stable = ''
    patch = 'patch'
    exp = 'exp'
    beta = 'beta'
    alpha = 'alpha'
    pre_releases_labels = ['alpha', 'beta', 'exp', 'patch']
    labels = ['stable', 'patch', 'rc', 'beta', 'alpha']
    LABEL_TO_CHANNEL = None
    CHANNEL_TO_LABEL = None


Channel.LABEL_TO_CHANNEL = {
    'stable': Channel.stable,
    'patch': Channel.patch,
    'rc': Channel.exp,
    'beta': Channel.beta,
    'alpha': Channel.alpha,
}

Channel.CHANNEL_TO_LABEL = {Channel.LABEL_TO_CHANNEL[k]: k for k in Channel.LABEL_TO_CHANNEL}
