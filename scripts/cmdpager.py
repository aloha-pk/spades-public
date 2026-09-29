#!/usr/bin/env python3
# Public domain.
from piqueserver.commands import command, has_permission, get_command_help, _commands
end=None

def apply_script(proto, con, config):
	return proto, con;
end

def print_cmd(con, x):
	desc, usage, _ = get_command_help(x);

	if (len(usage) != 0 and usage[0] != "/"):
		usage = "";
	end

	if (desc != ""):
		if (usage != ""):
			con.send_chat(usage + " -- " + desc + "\n");
		else:
			con.send_chat("/" + x.command_name + " -- " + desc + "\n");
		end
	else:
		if (usage != ""):
			con.send_chat(usage + "\n");
		else:
			con.send_chat("/" + x.command_name + "\n");
		end
	end
end

# TODO: this line length is a pile of crap. . .
@command("commands", "cmds")
def commands(con, pagearg=None):
	"""
	Prints an alphabetically ordered list of all commands.
	/commands [page]
	"""
	PAGER_SIZE = 5;

	cmds = [x for x in _commands.values() if has_permission(x, con)];
	cmds.sort(key=lambda x: x.command_name);

	if (pagearg is None):
		con.send_chat("Use `/cmds 1` for a pager view. Use `/cmds 0` for a non-compacted view.");
		con.send_chat("Available commands: " + ", ".join([x.command_name for x in cmds]));
		return;
	end

	pages = (len(_commands)+PAGER_SIZE-1)//PAGER_SIZE;
	page = int(pagearg) - 1;
	if (page < -1): page = -1;
	if (page >= pages): page = pages - 1;

	pagestart, pageend = 0, -1;
	if (page == -1):
		con.send_chat("Dumping all " + str(len(cmds)) + " commands that you have access to.");
	else:
		con.send_chat("Page " + str(page+1) + "/" + str(pages) + ("; Use `/cmds " + str(page+2) + "` for next page.\n" if page != pages - 1 else "\n"));
		pagestart, pageend = page*PAGER_SIZE, page*PAGER_SIZE+PAGER_SIZE;
	end

	for x in cmds[pagestart:pageend]:
		print_cmd(con, x);
	end
end

def apropos(con, *strarg):
	"""
	Filter through the list of commands.
	/apropos [string...]
	"""

	strful = " ".join(strarg);

	# TODO: aliases. . .
	cmds = [x for x in _commands.values() if has_permission(x, con) and strful in x.command_name];
	cmds.sort(key=lambda x: x.command_name);

	for x in cmds:
		print_cmd(con, x);
	end
end
