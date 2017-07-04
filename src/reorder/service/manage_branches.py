# coding=utf-8

from src.cfg import Config
from src.reorder.finder import FindProfile, FindBranch
from src.reorder.service import ConvertUrl
from src.reorder.value import BranchesModelContainer, Branch, Branches
from src.utils.gh import GHSession
from src.utils import ThreadPool


class ManageBranches:
    _GH_SESSION = None
    _WATCHERS = []
    _POOL = ThreadPool(1, 'ManageBranches', _daemon=True)

    @staticmethod
    def watch_branch_change(func: callable):
        ManageBranches._WATCHERS.append(func)

    @staticmethod
    def notify_watchers():
        for func in ManageBranches._WATCHERS:
            func()

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
    def _refresh_gh_branches():
        active_profile = FindProfile().get_active_profile()
        if active_profile:
            user, repo = ConvertUrl.convert_gh_url(active_profile.gh_repo)
            session = ManageBranches._get_gh_session()
            Branches().clear()
            Branches().append(Branch('All'))
            for branch in session.get_branches(user, repo):
                Branches().append(Branch(branch.name))
            ManageBranches._set_combo_model()
            ManageBranches._set_active_branch_for_current_profile()

    @staticmethod
    def refresh_gh_branches():

        def task_callback(*_):
            ManageBranches.notify_watchers()

        ManageBranches._POOL.queue_task(
            ManageBranches._refresh_gh_branches,
            _task_callback=task_callback
        )

    @staticmethod
    def _set_active_branch_for_current_profile():
        if Config().last_used_branch:
            try:
                last_used_branch = Config().last_used_branch[FindProfile.get_active_profile().name]
                if last_used_branch:
                    Branches.ACTIVE_BRANCH = FindBranch.get_by_name(last_used_branch)
            except ValueError:
                Branches.ACTIVE_BRANCH = FindBranch.get_by_name('All')

    @staticmethod
    def load_values_from_config():
        profile_name = Config().last_used_auto_profile
        if profile_name:
            ManageBranches.refresh_gh_branches()

    @staticmethod
    def change_active_branch(branch_name: str):
        branch = FindBranch.get_by_name(branch_name)
        Branches.ACTIVE_BRANCH = branch
        if Config().last_used_branch:
            d = dict(Config().last_used_branch)
        else:
            d = dict()
        d[FindProfile.get_active_profile().name] = branch_name
        Config().last_used_branch = d
        print(f'branch has changed to {branch_name}')
        ManageBranches.notify_watchers()
