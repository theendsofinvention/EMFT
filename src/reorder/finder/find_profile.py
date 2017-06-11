# coding=utf-8


from src.reorder.value import AutoProfile, AutoProfiles


class FindProfile:

    @staticmethod
    def get_by_name(name: str) -> AutoProfile:
        if name not in AutoProfiles():
            raise KeyError(f'output folder not registered: {name}')
        return AutoProfiles()[name]

    @staticmethod
    def get_active_profile() -> AutoProfile:
        return AutoProfiles.ACTIVE_PROFILE
