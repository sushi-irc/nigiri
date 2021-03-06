# coding: UTF-8
"""
Copyright (c) 2009 Marian Tietz
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""

import urwid
import logging

import connection
import commands
import signals
import config
import tabs
import messages
import __main__

# TODO: update plugin API to current version

# XXX:  maybe better proxy both, commands and signals,
# XXX:: to catch errors in the error code.

"""
TYPE_STRING: Takes one argument (default string)
TYPE_PASSWORD: Hidden string. Takes one argument (default string)
TYPE_NUMBER: Takes one argument (default number)
TYPE_BOOL: Takes one argument (default bool value)
TYPE_CHOICE: Takes n key/value tuple and a default index.
"""
(TYPE_STRING,
 TYPE_PASSWORD,
 TYPE_NUMBER,
 TYPE_BOOL,
 TYPE_CHOICE
) = range(5)

class Plugin (object):

	def __init__(self, plugin_name):
		self.__registered_signals = {}

		self._plugin_name = plugin_name

		urwid.connect_signal(connection.sushi, "connected", self.maki_connected)
		urwid.connect_signal(connection.sushi, "disconnected", self.maki_disconnected)

	def __register_signal(self, signal, handler):
		if self.__registered_signals.has_key(signal):
			self.__registered_signals[signal].append(handler)
		else:
			self.__registered_signals[signal] = [handler]

	def __unregister_signal(self, signal, handler):
		if self.__registered_signals[signal].has_key(signal):
			try:
				i = self.__registered_signals[signal].index(handler)
			except ValueError:
				return
			del self.__registered_signals[signal][i]

	def unload(self):
		for (signal, handlers) in self.__registered_signals.items():
			for handler in handlers:
				signals.disconnect_signal(signal, handler)

	def maki_connected(self, sushi):
		pass

	def maki_disconnected(self, sushi):
		pass

	def get_bus(self):
		return connection.sushi

	def get_nick(self, server):
		server_tab = __main__.main_window.find_server(server)
		if not server_tab:
			return None

		nick = server_tab.get_nick()

		if not nick:
			return None

		return nick

	def add_command(self, command, func):
		def func_proxy (main_window, argv):
			ct = main_window.current_tab

			if not ct:
				server_name = ""
				target_name = ""
			elif type(ct) == tabs.Server:
				server_name = ct.name
				target_name = ""
			else:
				server_name = tabs.get_server(ct).name
				target_name = ct.name

			return func(server_name, target_name, argv[1:])

#		self.emit("command_add", command, func)
		return commands.add_command(command, func_proxy)

	def remove_command(self, command):
#		self.emit("command_remove", command, func)
		return commands.remove_command(command)

	def connect_signal(self, signal, func):
#		self.emit("signal_connect", signal, func)
		self.__register_signal(signal,func)
		return signals.connect_signal(signal, func)

	def disconnect_signal(self, signal, func):
#		self.emit("signal_disconnect", signal, func)
		self.__unregister_signal(signal, func)
		return signals.disconnect_signal(signal, func)

	def set_config(self, name, value):
		section = "plugin_%s" % (self._plugin_name)

		config.create_section(section)

		return config.set(section, name, value)

	def get_config(self, name, default = None):
		section = "plugin_%s" % (self._plugin_name)

		return config.get(section, name, default)

	def display_error(self, error):
		logging.error("%s: %s" % (self._plugin_name, error))
		messages.print_error("%s: %s" % (self._plugin_name,error))

	def parse_from(self, host):
		return connection.parse_from(host)
