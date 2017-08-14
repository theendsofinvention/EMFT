# coding=utf-8


def initialize_updater(
    current_version,
    av_user,
    av_repo,
    local_executable,
    channel,
):
    from . import updater, channel
    from emft.config import Config

    try:
        channel = channel.LABEL_TO_CHANNEL[Config().update_channel]
    except KeyError:
        Config().update_channel = channel = 'beta'

    updater.updater = updater.Updater(**locals())
