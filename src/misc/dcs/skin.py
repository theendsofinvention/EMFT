# coding=utf-8
class DCSSkin:
    def __init__(self, name, ac, root_folder, skin_nice_name):
        self.name = name
        self.ac = ac
        self.root_folder = root_folder
        self.skin_nice_name = skin_nice_name or name

    def __repr__(self):
        return 'DCSSkin("{}", "{}", "{}", "{}")'.format(
            self.name, self.ac, self.root_folder, self.skin_nice_name
        )