#!/usr/bin/env python
# vi:tabstop=2:shiftwidth=2:expandtab
############################################
##  Licence: Public Domain
############################################

from dbus.mainloop.glib import DBusGMainLoop
import dbus
import gobject
import threading
import sys
import time
import signals
import commands

class Nigiri(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)        
    self.servers = []
    self.channels = {}
    self.nicks = {}
    self.own_nicks = {}
    self.current_server = "euirc" # TODO
    self.current_channel = "#Inkirei" # TODO
    self.commandlist = commands.get_commandlist()
    self.connection_retries = 12 # TODO client-config
    self.bus = None
    self.proxy = None
    self.loop = None
    self.start_client()

  def run(self):
    try:
      self.loop.run()
    except KeyboardInterrupt:
      self.loop.quit()

  def stop(self):
    self._Thread__stop()
    self.loop.quit()

  def start_client(self):
    print "connecting to dbus..."
    DBusGMainLoop(set_as_default=True)
    gobject.io_add_watch(sys.stdin, gobject.IO_IN | gobject.IO_ERR | gobject.IO_HUP, commands.input_handler, self)
    self.loop = gobject.MainLoop()
    self.bus = dbus.SessionBus()
  
    print "starting signal processing..."
    self.signals = signals.Signals(self)

    retry = 0
    while self.proxy == None and retry < self.connection_retries: 
      print "connecting to maki..."
      try:
        self.proxy = self.bus.get_object("de.ikkoku.sushi", "/de/ikkoku/sushi")
      except dbus.DBusException:
        retry += 1
        if retry < self.connection_retries:
          time.sleep(5)
          print "retry",
        else:
          print "connection failed!"
          sys.exit(1)
    
    print "retrieve information from maki"
    commands.servers(self, "")
    commands.own_nick(self, "")
    for server in self.servers:
      commands.channels(self, server)

if __name__ == "__main__":
  nigiri = Nigiri()
  nigiri.start()
