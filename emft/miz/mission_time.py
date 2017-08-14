# coding=utf-8

import datetime
import shutil

from emft.miz import Miz


class MissionTime:
    def __init__(self, moment: datetime.datetime):
        self.moment = moment
        print(moment.strftime('%d/%m/%Y %H:%M:%S'))

    def mission_start_time(self):
        return self.moment.strftime('%d/%m/%Y %H:%M:%S')


if __name__ == '__main__':
    time = MissionTime(datetime.datetime.now())
    with Miz('./test/test_files/time.miz') as miz:
        miz._encode()
        shutil.copy(miz.mission_file, './test/test_files/time/input')
        miz.mission.mission_start_time_as_date = time.mission_start_time()
        miz._encode()
        shutil.copy(miz.mission_file, './test/test_files/time/output')
        miz.zip('./test/test_files/time_output.miz')
