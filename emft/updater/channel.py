# coding=utf-8
STABLE = ''
PATCH = 'patch'
EXP = 'exp'
BETA = 'beta'
ALPHA = 'alpha'

VALID_CHANNELS = {'', 'patch', 'exp', 'beta', 'alpha'}
PRE_RELEASE_LABELS = ['alpha', 'beta', 'exp', 'patch']
LABELS = ['stable', 'patch', 'rc', 'beta', 'alpha']
LABEL_TO_CHANNEL = {
    'stable': STABLE,
    'patch': PATCH,
    'rc': EXP,
    'beta': BETA,
    'alpha': ALPHA,
}
CHANNEL_TO_LABEL = {LABEL_TO_CHANNEL[k]: k for k in LABEL_TO_CHANNEL}
