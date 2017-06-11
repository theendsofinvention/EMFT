def initialize():
    from .service import ManageOutputFolders
    ManageOutputFolders.read_output_folders_from_config()
    from .service import ManageProfiles
    ManageProfiles.read_profiles_from_config()
    from .service.manage_branches import ManageBranches
    ManageBranches.read_branches_from_config()
