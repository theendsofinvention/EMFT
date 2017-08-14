# coding=utf-8

import click


@click.command(help='test')
def _set_time():
    pass


@click.command(help='test')
@click.option('-t', '--time', help='Time of day', type=str, required=False)
@click.option('-d', '--date', help='Date', required=False)
def set_time(time, date):
    click.secho(_set_time(time, date))
