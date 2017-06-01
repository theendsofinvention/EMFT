from ..value.local_profiles import local_profiles
from ..value.reorder_profile import ReorderProfile
import typing
from utils import make_logger

logger = make_logger(__name__)


class FindLocalProfile:
    @staticmethod
    def find_profile_by_name(profile_name: str) -> ReorderProfile:
        try:
            return local_profiles[profile_name]
        except KeyError:
            logger.exception(f'profile not found: {profile_name}')
            raise

    @staticmethod
    def get_all_profiles_names() -> typing.List[str]:
        return local_profiles.profiles_names()
