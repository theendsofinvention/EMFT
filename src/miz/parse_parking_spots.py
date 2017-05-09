# coding=utf-8

import click
from collections import defaultdict, OrderedDict

@click.command()
@click.argument('miz_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def main(miz_path):

    from src.miz.miz import Miz
    with Miz(miz_path) as m:
        mis = m.mission

    result = defaultdict(dict)
    for unit in mis.units:
        airport, spot = unit.group_name.split('#')
        spot = int(spot)
        # print(airport, int(spot), unit.unit_position)
        result[airport][spot] = unit.unit_position

    import pickle
    with open('_parking_spots.py', mode='w') as f:
        f.write('parkings = {}'.format(pickle.dumps(result)))

    # # print(out)
    # import src.miz.out
    # with open('out.py') as f:
    #     res = pickle.loads(src.miz.out.parkings)

    # print(res)

    # for k in result:
    #     parkings[k] = result[k]
    #
    # parkings.write()


if __name__ == '__main__':
    main()



