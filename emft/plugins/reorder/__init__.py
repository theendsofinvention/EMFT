# coding=utf-8


def initialize():
    from emft.plugins.reorder.service import ManageOutputFolders, ManageBranches, ManageProfiles, ManageRemoteVersions
    ManageProfiles.watch_profile_change(ManageBranches.refresh_gh_branches)
    ManageBranches.watch_branch_change(ManageRemoteVersions.get_latest_remote_version)
    ManageOutputFolders.read_output_folders_from_config()
    ManageProfiles.read_profiles_from_config()
    ManageBranches.load_values_from_config()
