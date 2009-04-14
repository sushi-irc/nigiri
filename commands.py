
import tabs
from typecheck import types
from messages import print_notification, print_error, print_normal
import config

import connection

def no_connection():
	if not connection.is_connected():
		print_error("No connection to maki.")
		return True
	return False

def send_text(tab, text):
	if no_connection() or type(tab) == tabs.Server:
		return

	server_name = tab.parent.name

	if not tab.connected:
		print_error("Not connected to server "\
			"'%s'." % (server_name))
		return

	if type(tab) == tabs.Channel and not tab.joined:
		print_error("You are not on the channel "\
			"'%s'." % (tab.name))
		return

	connection.sushi.message(server_name, tab.name, text)

def cmd_add_server(main_window, argv):
	""" /add_server <name> <address> <port> <nick> <real> """
	if no_connection():
		return

	if len(argv) != 6:
		print_notification("Usage: /add_server <name> <address> "\
			"<port> <nick> <real>")
		return

	cmd, server_name, address, port, nick, name = argv

	try:
		int(port)
	except ValueError:
		print_error("Invalid value for 'port' given.")
		return

	if server_name in connection.sushi.server_list("",""):
		print_error("Server with name '%s' already existing." % (server_name))
		return

	pairs = (("address", address), ("port", port), ("nick", nick),
		("name", name))
	for key,value in pairs:
		connection.sushi.server_set(server_name, "server", key, value)

	print_notification("Server '%s' successfully added." % (server_name))

def cmd_close(main_window, argv):
	""" /close """
	# close the current tab
	if not main_window.current_tab:
		return

	to_delete = main_window.current_tab
	main_window.switch_to_next_tab()
	to_delete.remove()

def cmd_connect(main_window, argv):
	""" /connect <server> """
	if no_connection():
		return

	if len(argv) != 2:
		print_notification("Usage: /connect <server>")
		return

	if argv[1] not in connection.sushi.server_list("",""):
		print_error("connect: The server '%(server)s' is not known." % {
			"server": argv[1]})
		return

	connection.sushi.connect(argv[1])

def cmd_echo(main_window, argv):
	""" /echo <text> """
	main_window.print_text(" ".join(argv[1:])+"\n")

def cmd_join(main_window, argv):
	""" /join <channel> [<key>] """
	if len(argv) == 3:
		cmd, channel, key = argv
	elif len(argv) == 2:
		cmd, channel = argv
		key = ""
	else:
		print_notification("Usage: /join <channel> [<key>]")
		return

	server_tab = tabs.get_server(main_window.current_tab)

	if not server_tab:
		print_error("No tab active.")
		return

	connection.sushi.join(server_tab.name, channel, key)
	print_notification("Joining channel '%s'." % (channel))

def cmd_maki(main_window, argv):
	""" /maki [connect|shutdown] """
	def usage():
		print_notification("Usage: /maki [connect|shutdown]")

	if len(argv) != 2:
		usage()
		return

	cmd = argv[1]

	if cmd == "connect":
		print_notification("Connection to maki...")

		if connection.connect():
			print_notification("Connection to maki etablished.")
		else:
			print_notification("Connection to maki failed.")
		main_window.update_divider()

	elif cmd == "disconnect":
		if no_connection():
			return

		connection.disconnect()
		print_notification("Disconnected from maki.")
		main_window.update_divider()

	elif cmd == "shutdown":
		if no_connection():
			return

		connection.sushi.shutdown(config.get("chatting", "quit_message"))
		main_window.update_divider()

	else:
		usage()
		return

def cmd_overview(main_window, argv):
	""" /overview [<server>] """
	if no_connection():
		return

	if len(argv) == 2:
		if argv[1] not in [n.name for n in main_window.servers]:
			print_error("Server '%s' not found." % (argv[1]))
			return
		server_list = [main_window.find_server(argv[1])]
	else:
		server_list = main_window.servers

	print_normal("Begin overview.")

	for server in server_list:
		if server.connected:
			connected = "connected"
		else:
			connected = "not connected"

		print_normal("Server '%s' (%s)" % (server, connected))

		for child in server.children:
			if type(child) == tabs.Channel:
				if child.joined:
					joined = "joined"
				else:
					joined = "not joined"
				print_normal("- Channel '%s' (%s)" % (child.name, joined))
			else:
				print_normal("- Query '%s'" % (child.name))

	print_normal("End of overview.")

def cmd_python(main_window, argv):
	""" /python <code> """
	print_notification ("python: Executing...\n")
	try:
		exec(" ".join(argv[1:]))
	except BaseException,e:
		print_error ("python: %s\n" % (e))

def cmd_quit(main_window, argv):
	""" /quit """
	main_window.quit()

def cmd_remove_server(main_window, argv):
	""" /remove_server <name> """
	if no_connection():
		return

	if len(argv) != 2:
		print_notification("Usage: /remove_server <name>")
		return

	name = argv[1]

	if not name in connection.sushi.server_list("", ""):
		print_error("Server '%s' not known to maki." % (name))
		return

	connection.sushi.server_remove(name, "", "")
	print_notification("Server '%s' successfully removed." % (name))

def cmd_servers(main_window, argv):
	""" /servers """
	if no_connection():
		return

	active_servers = connection.sushi.servers()

	print_normal("Servers known to maki: ")
	for name in connection.sushi.server_list("",""):
		if name in active_servers:
			connected = "connected"
		else:
			connected = "not connected"
		print_normal("- '%s' (%s)" % (name, connected))

_command_dict = {
	"add_server": cmd_add_server,
	"close": cmd_close,
	"connect": cmd_connect,
	"echo": cmd_echo,
	"join": cmd_join,
	"maki": cmd_maki,
	"overview": cmd_overview,
	"python": cmd_python,
	"quit": cmd_quit,
	"remove_server": cmd_remove_server,
	"servers": cmd_servers
}

_builtins = _command_dict.keys()

@types (cmd=str)
def strip_command_char (cmd):
	if not cmd: return cmd
	if cmd[0] != config.get("nigiri","command_char"):
		return cmd
	return cmd[1:]

@types (text=str)
def parse(main_window, text):
	argv = text.split(" ")

	if (not argv
		or (argv[0]
			and argv[0][0] != config.get(
				"nigiri",
				"command_char"))):
		return False

	command = strip_command_char (argv[0])

	if not command:
		return False

	try:
		fun = _command_dict[command]
	except KeyError:
		print_error ("No such command '%s'.\n" % (command))
	else:
		fun (main_window, argv)

	return True

@types (name=str, fun=type(lambda:""))
def add_command(name, fun):
	global _command_dict
	if _command_dict.has_key (name):
		return False
	_command_dict[name] = fun

@types (name=str)
def remove_command(name):
	global _command_dict
	if _command_dict.has_key (name) and name not in _builtins:
		del _command_dict[name]
		return True
	return False
