from utils import Path

from ..value import local_profiles
from ..value.reorder_profile import ReorderProfile


class CollectLocalProfiles:
    @staticmethod
    def collect_local_profiles(path: str = '.'):
        profiles = dict()
        for file in Path(path).listdir('*.profile'):
            file_path = Path(file)
            profile_name = file_path.namebase
            profiles[profile_name] = ReorderProfile(profile_name)
        local_profiles.local_profiles = local_profiles.LocalProfiles(init_dict=profiles)
