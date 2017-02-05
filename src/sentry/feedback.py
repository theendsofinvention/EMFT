# coding=utf-8

from src.cfg.cfg import Config
from src.sentry.sentry import SENTRY


def send_feedback(msg: str, msg_type: str):
    SENTRY.extra_context(
        data={
            # 'user': Config().usr_name,
            # 'mail': Config().usr_email,
        }
    )
    text = '{}\n{}'.format(msg_type, msg)
    SENTRY.captureMessage(
        message=text, level='debug',
        tags={
            'message': msg_type,
            'type': 'message',
        }
    )
