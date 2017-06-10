# coding=utf-8

from src.cfg import Config
from src.reorder.service import ConvertUrl
from src.reorder.value import ReorderProfile, ReorderProfiles, AutoProfileModelContainer
from src.utils import Path, make_logger

logger = make_logger(__name__)


class ManageProfiles:
    @staticmethod
    def _set_combo_model():
        logger.debug('resetting combo model')
        model = AutoProfileModelContainer().model
        model.beginResetModel()
        model.clear()
        for name in ReorderProfiles().keys():
            logger.debug(f'adding profile {name}')
            model.appendRow(name)
        model.endResetModel()

    @staticmethod
    def write_profiles_to_config():
        d = dict()
        for name, profile in ReorderProfiles().items():
            d[name] = (profile.gh_repo, profile.av_repo, profile.src_folder, profile.output_folder)
        Config().reorder_auto_profiles = d

    @staticmethod
    def read_profiles_from_config():
        if Config().reorder_auto_profiles:
            for name, values in Config().reorder_auto_profiles.items():
                profile = ReorderProfile(
                    name=name,
                    gh_repo=values[0],
                    av_repo=values[1],
                    src_folder=values[2],
                    output_folder=values[3],
                )
                ReorderProfiles()[name] = profile
            ManageProfiles._set_combo_model()

    @staticmethod
    def add_profile_from_values(
            name: str,
            gh_repo: str,
            av_repo: str,
            src_folder: str,
            output_folder: str,
    ) -> bool:
        profile = ReorderProfile(
            name=name,
            gh_repo=gh_repo,
            av_repo=av_repo,
            src_folder=src_folder,
            output_folder=output_folder
        )
        return ManageProfiles.add_profile_object(name, profile)

    @staticmethod
    def add_profile_object(name: str, profile: ReorderProfile) -> bool:
        src_folder = Path(profile.src_folder)
        output_folder = Path(profile.output_folder)
        if name in ReorderProfiles():
            raise FileExistsError(f'a profile is already registered with that name: {name}')
        if not src_folder.exists():
            raise FileNotFoundError(f'the source folder does not exist: {src_folder.abspath()}')
        if not output_folder.exists():
            raise FileNotFoundError(f'the output folder does not exist: {src_folder.abspath()}')

        # ConvertURL will raise a ValueError if this fail
        ConvertUrl.convert_gh_url(profile.gh_repo)
        ConvertUrl.convert_av_url(profile.av_repo)

        logger.debug(f'adding profile: {name}')
        ReorderProfiles()[name] = profile
        ManageProfiles._set_combo_model()
        ManageProfiles.write_profiles_to_config()
        return True

    @staticmethod
    def get_by_name(name: str):
        if name not in ReorderProfiles():
            raise KeyError(f'output folder not registered: {name}')
        return ReorderProfiles()[name]

    @staticmethod
    def remove_output_folder(name: str):
        if name not in ReorderProfiles():
            raise KeyError(f'output folder not registered: {name}')
        del ReorderProfiles()[name]
        ManageProfiles._set_combo_model()
        ManageProfiles.write_profiles_to_config()
