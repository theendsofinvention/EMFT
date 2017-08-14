# coding=utf-8

import click


@click.command(help='test')
def set_time():
    pass


@click.command(help='test')
@click.option('-t', '--time', help='Time of day', type=str, required=False)
@click.option('-d', '--date', help='Date', required=False)
def set_time(time, date):
    click.secho(set_time(time, date))