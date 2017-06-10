def initialize():
    from .service import ManageOutputFolders
    ManageOutputFolders.read_output_folders_from_config()
