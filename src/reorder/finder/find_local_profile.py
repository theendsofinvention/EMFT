import typing

from src.utils import make_logger
from ..value.local_profiles import LOCAL_PROFILES
from ..value.reorder_profile import ReorderProfile

logger = make_logger(__name__)


class FindLocalProfile:
    @staticmethod
    def local_profile_exists(profile_name: str) -> bool:
        return profile_name in LOCAL_PROFILES.keys()

    @staticmethod
    def find_profile_by_name(profile_name: str) -> ReorderProfile:
        try:
            return LOCAL_PROFILES[profile_name]
        except KeyError:
            logger.exception(f'profile not found: {profile_name}')
            raise

    @staticmethod
    def get_all_profiles_names() -> typing.List[str]:
        return LOCAL_PROFILES.profiles_names()
