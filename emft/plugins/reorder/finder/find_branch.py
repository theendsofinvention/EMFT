# coding=utf-8


from emft.plugins.reorder.value import Branch, Branches


class FindBranch:
    @staticmethod
    def get_active_branch() -> Branch:
        return Branches.ACTIVE_BRANCH

    @staticmethod
    def get_by_name(branch_name: str) -> Branch:
        for branch in Branches():
            if branch_name == branch.name:
                return branch
        raise ValueError(f'no branch named: {branch_name}')
