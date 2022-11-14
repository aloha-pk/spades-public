# Copyrights for portions of this file are held by one or more contributors from the Ace of Spades community.
# All other copyrights are held jointly by collaborators from the aloha.pk community.
# This file is a redistribution by the aloha.pk organization. More information: https://aloha.pk/pub/github-org

"""
Command helper.
Copyright (c) 2013 learn_more
See the file license.txt or http://opensource.org/licenses/MIT for copying permission.

Lists all commands available to you (permission based).
"""

from piqueserver.commands import command, has_permission, _commands, _alias_map


@command()
def commands(connection):
    """
    Shows available commands
    /commands
    """
    names = []
    cmds = sorted(_commands.keys())
    for cmd_name in cmds:
        cmd_func = _commands[cmd_name]
        if not has_permission(cmd_func, connection):
            continue
        aliases = [alias for alias in _alias_map if _alias_map[alias] == cmd_name]
        if aliases:
            cmd = f"{cmd_name} ({', '.join(aliases)})"
        else:
            cmd = cmd_name
        names.append(cmd)

    return f"Commands: {', '.join(names)}"


def apply_script(protocol, connection, config):
    return protocol, connection
