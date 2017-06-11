def initialize():
    from .service import ManageOutputFolders, ManageBranches, ManageProfiles, ManageRemoteVersions
    ManageProfiles.watch_profile_change(ManageBranches.refresh_gh_branches)
    ManageBranches.watch_branch_change(ManageRemoteVersions.get_latest_remote_version)
    ManageOutputFolders.read_output_folders_from_config()
    ManageProfiles.read_profiles_from_config()
    ManageBranches.read_branches_from_config()
