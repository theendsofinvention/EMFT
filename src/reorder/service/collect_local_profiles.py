from src.utils import Path, make_logger

from src.reorder.value import local_profiles, ReorderProfile

logger = make_logger(__name__)


class CollectLocalProfiles:
    @staticmethod
    def collect_local_profiles(path: str = '.'):
        logger.debug('collecting local profiles')
        profiles = dict()
        for file in Path(path).listdir('*.profile'):
            logger.debug(f'found profile file: {file}')
            file_path = Path(file)
            profile_name = file_path.namebase
            profiles[profile_name] = ReorderProfile(profile_name)
        local_profiles.LOCAL_PROFILES = local_profiles.LocalProfiles(init_dict=profiles)
