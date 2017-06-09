# coding=utf-8

from src.cfg import Config
from src.reorder import value
from src.reorder.finder.find_local_profile import FindLocalProfile
from src.ui.main_ui import I
from src.utils import make_logger

logger = make_logger(__name__)


class ChangeActiveProfile:
    @staticmethod
    def change_active_profile(new_profile_name):
        if FindLocalProfile.local_profile_exists(new_profile_name):
            I.tab_reorder_change_active_profile(new_profile_name)
            Config().reorder_last_profile_name = new_profile_name
        else:
            logger.error(f'profile does not exist: {new_profile_name}')

    @staticmethod
    def restore_last_profile_from_config():
        if Config().reorder_last_profile_name:
            value.ACTIVE_PROFILE = FindLocalProfile.find_profile_by_name(Config().reorder_last_profile_name)
