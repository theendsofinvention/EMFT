from src.miz import Miz
import pprint
from src.miz.service.convert_coord import ConvertCoord

def main():
    with Miz('draw.miz') as m:
        for group in m.mission.groups:
            group_name = group.group_name
            if group_name.startswith('$$DRAW_'):
                # pprint.pprint(group.group_route._section_route)
                for point in group.group_route.points:
                    print(ConvertCoord.convert_point(point))
                    # print(point.name)
                    # print(point.x)
                    # print(point.y)
                    # pprint.pprint(point._point)
                    # break
                    # print(point.action)
                break


if __name__ == '__main__':
    main()