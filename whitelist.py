import click
import json
import os
from enum import Enum
from typing import Dict, List
from mcrcon import MCRcon
from mojang import MojangAPI


class Keys(Enum):
    DESTINATIONS = 1
    PATHS = 2
    OBJ = 3


class Whitelist:
    """Class represents whitelist object to modify inside script and export to json"""

    def __init__(self, path: str = 'whitelist.json'):
        self.path: str = path
        self._usernames: Dict[str, str] = {}
        self.__container: List[Dict] = []
        if not os.path.exists(path):
            self.save()
        else:
            self.load()

    def save(self) -> None:
        """Export whitelist container to json path"""
        self._update_container()
        with open(self.path, mode='w') as file:
            json.dump(self.__container, file, indent=2)

    def load(self) -> None:
        """Load whitelist container from json path"""
        with open(self.path, mode='r') as file:
            self.__container = json.load(file)
            self._usernames = {item['name']: item['uuid']
                               for item in self.__container}

    def _update_container(self):
        """Update inner container from _usernames"""
        self.__container = [
            {
                "uuid": uuid,
                "name": name
            } for name, uuid in self._usernames.items()
        ]

    def __str__(self) -> str:
        return f'Whitelist with {len(self._usernames)} usernames: ' \
            ", ".join([name for name in self._usernames.keys()])

    def add(self, targets: List[str]) -> None:
        """Add usernames to whitelist

        Args:
            targets (List[str]): usernames to add
        """
        update = {}
        for target in targets:
            try:
                update[target] = Whitelist.id_to_uuid(
                    MojangAPI.get_uuid(username=target))
                print(f'Added {target} to whitelist')
            except Exception as e:
                pass
        self._usernames.update(update)
        self.save()

    def remove(self, targets: List[str]) -> None:
        """Remove usernames to whitelist

        Args:
            targets (List[str]): usernames to remove
        """
        for target in targets:
            if target in self._usernames:
                self._usernames.pop(target)
                print(f'Removed {target} from whitelist')
        self.save()

    def list(self):
        """Prints list of whitelisted players"""
        print(f'There are {len(self._usernames)} whitelisted players:',
              ", ".join([name for name in self._usernames.keys()]))

    @staticmethod
    def id_to_uuid(id_):
        """Add dashes to id

        >>> Whitelist.id_to_uuid("bb9b450bdc414e5eaafd57bcfbf98617")
        "bb9b450b-dc41-4e5e-aafd-57bcfbf98617"

        Args:
            id_ (str): id
        """
        batches = []
        ind = 0
        for n in [8, 4, 4, 4, 12]:
            batches.append(id_[ind:ind + n])
            ind += n
        return '-'.join(batches)


def send_command_to_mcrcon(command: str, host: str = 'localhost', port: int = 25575, password: str = '', tlsmode=0, **kwargs) -> str:
    try:
        with MCRcon(host, password, port, tlsmode) as mcr:
            try:
                return mcr.command(command)
            except (ConnectionResetError, ConnectionAbortedError):
                return "The connection was terminated, the server may have been stopped."
    except ConnectionRefusedError:
        return "The connection could not be made as the server actively refused it."
    except ConnectionError as e:
        return repr(e)


@click.group()
@click.option('--config_path', default='whitelist_config.json', show_default=True, type=click.Path(exists=True, readable=True))
@click.pass_context
def whitelist(ctx, config_path):
    """This script prints maintains whitelist on multiple servers.

        You can use mcrcon for native whitelist server command or
        use unified whitelist.json and create symlinks to all servers 
    """
    ctx.ensure_object(dict)
    with open(config_path, mode='r', encoding='utf8') as file:
        config = json.load(file)
        ctx.obj[Keys.DESTINATIONS] = config['destinations']
        ctx.obj[Keys.PATHS] = config['paths']


@whitelist.group()
@click.pass_context
def rcon(ctx):
    """Uses MCRcon for commands, pickups server's credentials from config_path"""
    pass


@whitelist.group()
@click.option('--whitelist_path', default='whitelist.json', show_default=True, type=click.Path())
@click.pass_context
def manual(ctx, whitelist_path):
    """Uses local whitelist.json and manipulates with it"""
    ctx.obj[Keys.OBJ] = Whitelist(whitelist_path)


@manual.command()
@click.argument('targets', nargs=-1, required=True, type=click.STRING)
@click.pass_context
def add(ctx, targets):
    """Add usernames to whitelist"""
    ctx.obj[Keys.OBJ].add(targets)


@manual.command()
@click.argument('targets', nargs=-1, required=True, type=click.STRING)
@click.pass_context
def remove(ctx, targets):
    """Remove usernames to whitelist"""
    ctx.obj[Keys.OBJ].remove(targets)


@manual.command()
@click.pass_context
def list(ctx):
    """Print whitelisted usernames"""
    ctx.obj[Keys.OBJ].list()


@rcon.command()
@click.argument('targets', nargs=-1, required=True, type=click.STRING)
@click.pass_context
def add(ctx, targets):
    """Add usernames to whitelist"""
    cmd = f'/whitelist add {" ".join(targets)}'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


@rcon.command()
@click.argument('targets', nargs=-1)
@click.pass_context
def remove(ctx, targets):
    """Remove usernames to whitelist"""
    cmd = f'/whitelist remove {" ".join(targets)}'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


@rcon.command()
@click.pass_context
def list(ctx):
    """Print whitelisted usernames"""
    cmd = '/whitelist list'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


@rcon.command()
@click.pass_context
def on(ctx):
    """On whitelist on servers"""
    cmd = '/whitelist on'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


@rcon.command()
@click.pass_context
def off(ctx):
    """Off whitelist on servers"""
    cmd = '/whitelist off'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


@rcon.command()
@click.pass_context
def reload(ctx):
    """Reload whitelist on servers"""
    cmd = '/whitelist reload'
    for dest in ctx.obj[Keys.DESTINATIONS]:
        click.echo(f'Command to {dest["name"]}')
        click.echo(send_command_to_mcrcon(cmd, **dest))


if __name__ == '__main__':
    whitelist(obj={})
