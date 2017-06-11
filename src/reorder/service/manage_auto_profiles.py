# coding=utf-8

import typing
from src.cfg import Config
from src.reorder.service import ConvertUrl
from src.reorder.value import AutoProfile, AutoProfiles, AutoProfileModelContainer
from src.reorder.finder import FindProfile
from src.utils import Path, make_logger

logger = make_logger(__name__)


class ManageProfiles:

    @staticmethod
    def _set_combo_model():
        logger.debug('resetting combo model')
        model = AutoProfileModelContainer().model
        model.beginResetModel()
        model.clear()
        for name in AutoProfiles().keys():
            logger.debug(f'adding profile {name}')
            model.appendRow(name)
        model.endResetModel()

    @staticmethod
    def write_profiles_to_config():
        d = dict()
        for name, profile in AutoProfiles().items():
            d[name] = (profile.gh_repo, profile.av_repo, profile.src_folder, profile.output_folder)
        Config().reorder_auto_profiles = d

    @staticmethod
    def read_profiles_from_config():
        if Config().reorder_auto_profiles:
            for name, values in Config().reorder_auto_profiles.items():
                profile = AutoProfile(
                    name=name,
                    gh_repo=values[0],
                    av_repo=values[1],
                    src_folder=values[2],
                    output_folder=values[3],
                )
                AutoProfiles()[name] = profile
            ManageProfiles._set_combo_model()
        if Config().last_used_auto_profile:
            ManageProfiles().change_active_profile(Config().last_used_auto_profile)

    @staticmethod
    def add_profile_from_values(
            name: str,
            gh_repo: str,
            av_repo: str,
            src_folder: str,
            output_folder: str,
    ) -> bool:
        profile = AutoProfile(
            name=name,
            gh_repo=gh_repo,
            av_repo=av_repo,
            src_folder=src_folder,
            output_folder=output_folder
        )
        return ManageProfiles.add_profile_object(name, profile)

    @staticmethod
    def add_profile_object(name: str, profile: AutoProfile) -> bool:
        src_folder = Path(profile.src_folder)
        output_folder = Path(profile.output_folder)
        if name in AutoProfiles():
            raise FileExistsError(f'a profile is already registered with that name: {name}')
        if not src_folder.exists():
            raise FileNotFoundError(f'the source folder does not exist: {src_folder.abspath()}')
        if not output_folder.exists():
            raise FileNotFoundError(f'the output folder does not exist: {src_folder.abspath()}')

        # ConvertURL will raise a ValueError if this fail
        ConvertUrl.convert_gh_url(profile.gh_repo)
        ConvertUrl.convert_av_url(profile.av_repo)

        logger.debug(f'adding profile: {name}')
        AutoProfiles()[name] = profile
        ManageProfiles._set_combo_model()
        ManageProfiles.write_profiles_to_config()
        return True

    @staticmethod
    def change_active_profile(profile_name: str):
        profile = FindProfile.get_by_name(profile_name)
        Config().last_used_auto_profile = profile_name
        AutoProfiles.ACTIVE_PROFILE = profile

    @staticmethod
    def get_gh_repo_info() -> typing.Tuple[str, str]:
        return ConvertUrl.convert_gh_url(FindProfile.get_active_profile().gh_repo)

    @staticmethod
    def get_av_repo_info() -> typing.Tuple[str, str]:
        return ConvertUrl.convert_av_url(FindProfile.get_active_profile().av_repo)

    @staticmethod
    def remove_profile(profile: AutoProfile or str) -> bool:
        if isinstance(profile, AutoProfile):
            profile = profile.name
        if profile not in AutoProfiles():
            raise KeyError(f'output folder not registered: {profile}')
        del AutoProfiles()[profile]
        ManageProfiles._set_combo_model()
        ManageProfiles.write_profiles_to_config()
        return True
