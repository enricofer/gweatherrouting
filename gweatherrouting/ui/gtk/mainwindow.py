# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

# TODO:
# https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/

import time
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk

from ... import log
from .settingswindow import SettingsWindow
from .projectpropertieswindow import ProjectPropertiesWindow
from .gribmanagerwindow import GribManagerWindow
from .maplayers import GribMapLayer, AISMapLayer

from .mainwindow_poi import MainWindowPOI
from .mainwindow_track import MainWindowTrack
from .mainwindow_routing import MainWindowRouting
from .mainwindow_time import MainWindowTime

class MainWindow(MainWindowPOI, MainWindowTrack, MainWindowRouting, MainWindowTime):
	def create (core):
		return MainWindow(core)

	def __init__(self, core):
		self.core = core

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/mainwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object("main-window")
		self.window.connect("delete-event", self.quit)
		self.window.set_default_size (1024, 600)
		self.window.show_all()
		# self.window.maximize ()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.gribMapLayer = GribMapLayer (self.core.gribManager)
		self.map.layer_add (self.gribMapLayer)
		self.map.layer_add (OsmGpsMap.MapOsd (show_dpad=True, show_zoom=True, show_crosshair=False))

		# self.map.gps_add(39,9,99)

		self.statusbar = self.builder.get_object("status-bar")

		MainWindowTime.__init__(self)
		MainWindowRouting.__init__(self)
		MainWindowTrack.__init__(self)
		MainWindowPOI.__init__(self)

		Gdk.threads_init()


	def quit(self, a, b):
		MainWindowRouting.__del__(self)
		Gtk.main_quit()


	def onMapClick(self, map, event):
		lat, lon = map.get_event_location (event).get_degrees ()
		self.builder.get_object("track-add-point-lat").set_text (str (lat))
		self.builder.get_object("track-add-point-lon").set_text (str (lon))
		self.statusbar.push(self.statusbar.get_context_id ('Info'), "Clicked on " + str(lat) + " " + str(lon))
		
		if event.button == 3:
			menu = self.builder.get_object("map-context-menu")
			menu.popup (None, None, None, None, event.button, event.time)
		self.map.queue_draw ()


	def onNew (self, widget):
		self.core.trackManager.create()
		self.updateTrack ()
		self.map.queue_draw ()



	# TODO: handle also grib import
	def onImport (self, widget):
		dialog = Gtk.FileChooserDialog ("Please choose a file", self.window,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			
		filter_gpx = Gtk.FileFilter ()
		filter_gpx.set_name ("GPX track")
		filter_gpx.add_mime_type ("application/gpx+xml")
		filter_gpx.add_pattern ('*.gpx')
		dialog.add_filter (filter_gpx)

		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			dialog.destroy ()

			if self.core.trackManager.importTrack (filepath):
				# self.builder.get_object('header-bar').set_subtitle (filepath)
				self.updateTrack ()
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
				edialog.format_secondary_text ("File opened, loaded %d waypoints" % len (self.core.trackManager.activeTrack))
				edialog.run ()
				edialog.destroy ()	
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Loaded %s with %d waypoints' % (filepath, len (self.core.trackManager.activeTrack)))					
				
			else:
				edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
		else:
			dialog.destroy()


	def onAbout(self, item):
		dialog = self.builder.get_object('about-dialog')
		response = dialog.run ()
		dialog.hide ()

	def onSettings(self, event):
		w = SettingsWindow.create ()
		w.show ()

	def onProjectProperties(self, event):
		w = ProjectPropertiesWindow.create ()
		w.show ()

	def onGribManager(self, event):
		w = GribManagerWindow.create (self.core.gribManager)
		w.show ()
