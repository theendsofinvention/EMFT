# coding=utf-8

from src.cfg import Config
from src.reorder.service import ManageProfiles
from src.reorder.value import BranchesModelContainer, Branch, Branches
from src.reorder.finder import FindProfile
from src.utils.gh import GHSession


class ManageBranches:
    _GH_SESSION = None
    _ACTIVE_BRANCH = None

    @staticmethod
    def get_active_branch() -> Branch:
        if ManageBranches._ACTIVE_BRANCH:
            return ManageBranches.get_by_name(ManageBranches._ACTIVE_BRANCH)

    @staticmethod
    def _set_combo_model():
        model = BranchesModelContainer().model
        model.beginResetModel()
        model.clear()
        for branch in Branches():
            model.appendRow(branch.name)
        model.endResetModel()

    @staticmethod
    def _get_gh_session() -> GHSession:
        if ManageBranches._GH_SESSION is None:
            ManageBranches._GH_SESSION = GHSession()
        return ManageBranches._GH_SESSION

    @staticmethod
    def refresh_gh_branches():
        active_profile = FindProfile().get_active_profile()
        if active_profile:
            user, repo = ManageProfiles.get_gh_repo_info()
            session = ManageBranches._get_gh_session()
            Branches().clear()
            Branches().append(Branch('All'))
            for branch in session.get_branches(user, repo):
                Branches().append(Branch(branch.name))
            ManageBranches._set_active_branch_for_current_profile()
            ManageBranches._set_combo_model()

    @staticmethod
    def get_by_name(branch_name: str) -> Branch:
        for branch in Branches():
            if branch_name == branch.name:
                return branch
        raise ValueError(f'no branch named: {branch_name}')

    @staticmethod
    def _set_active_branch_for_current_profile():
        if Config().last_used_branch:
            try:
                last_used_branch = Config().last_used_branch[FindProfile.get_active_profile().name]
                if last_used_branch:
                    ManageBranches._ACTIVE_BRANCH = last_used_branch
            except KeyError:
                ManageBranches._ACTIVE_BRANCH = 'All'

    @staticmethod
    def read_branches_from_config():
        profile_name = Config().last_used_auto_profile
        if profile_name:
            ManageProfiles.change_active_profile(profile_name)
            ManageBranches.refresh_gh_branches()
            ManageBranches._set_active_branch_for_current_profile()

    @staticmethod
    def change_active_branch(branch_name: str):
        ManageBranches.get_by_name(branch_name)
        ManageBranches._ACTIVE_BRANCH = branch_name
        if Config().last_used_branch:
            d = dict(Config().last_used_branch)
        else:
            d = dict()
        d[FindProfile.get_active_profile().name] = branch_name
        Config().last_used_branch = d
