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

import time
import gi
import math
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

from ... import config
from .aboutdialog import AboutDialog
from .routingwizarddialog import RoutingWizardDialog
from .gribselectdialog import GribSelectDialog
from .gribmaplayer import GribMapLayer
from .isochronesmaplayer import IsochronesMapLayer



class MainWindow:
	def create (core):
		return MainWindow(core)

	def __init__(self, core):
		self.selectedTrackItem = None
		self.core = core

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/mainwindow.glade")
		self.builder.connect_signals(self)

		window = self.builder.get_object("main-window")
		window.connect("delete-event", Gtk.main_quit)
		window.show_all()

		window.set_default_size (800, 600)
		window.maximize ()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.isochronesMapLayer = IsochronesMapLayer ()
		self.map.layer_add (self.isochronesMapLayer)
		self.gribMapLayer = GribMapLayer (self.core.grib)
		self.map.layer_add (self.gribMapLayer)
		self.map.layer_add (OsmGpsMap.MapOsd (show_dpad=True, show_zoom=True, show_crosshair=False))

		self.statusbar = self.builder.get_object("status-bar")
		self.trackStore = self.builder.get_object("track-list-store")


	def updateTrack (self):
		self.trackStore.clear ()
		self.map.track_remove_all ()
		track = OsmGpsMap.MapTrack ()

		#TODO: make it editable? should swap values between track and core model
		#track.set_property ("editable", True)
		track.set_property ("line-width", 2)

		i = 0
		for wp in self.core.getTrack ():
			i += 1
			self.trackStore.append([i, wp[0], wp[1]])

			p = OsmGpsMap.MapPoint ()
			p.set_degrees (wp[0], wp[1])
			track.add_point (p)
		self.map.track_add (track)


	def onTrackItemClick(self, item, event):
		if event.button == 3 and self.core.getTrack().size() > 0:
			menu = self.builder.get_object("track-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)

	def onSelectTrackItem (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			value = store.get_value(tree_iter, 0)
			self.selectedTrackItem = int(value) - 1
			print ('Selected: ', self.selectedTrackItem)

	def onTrackItemMoveUp(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().moveUp(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemMoveDown(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().moveDown(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemRemove(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().remove(self.selectedTrackItem)
			self.updateTrack()

	def onTrackItemDuplicate(self, widget):
		if self.selectedTrackItem != None:
			self.core.getTrack().duplicate(self.selectedTrackItem)
			self.updateTrack()


	def onMapClick(self, map, event):
		lat, lon = map.get_event_location (event).get_degrees ()
		self.builder.get_object("track-add-point-lat").set_text (str (lat))
		self.builder.get_object("track-add-point-lon").set_text (str (lon))
		self.statusbar.push(self.statusbar.get_context_id ('Info'), "Clicked on " + str(lat) + " " + str(lon))
		
		if event.button == 3:
			menu = self.builder.get_object("map-context-menu")
			menu.popup (None, None, None, None, event.button, event.time)


	def showTrackPointPopover(self, event):
		popover = self.builder.get_object("track-add-point-popover")
		popover.show_all()


	def addTrackPoint (self, widget):
		lat = self.builder.get_object("track-add-point-lat").get_text ()
		lon = self.builder.get_object("track-add-point-lon").get_text ()

		if len (lat) > 1 and len (lon) > 1:
			self.core.getTrack ().add (float (lat), float (lon))
			self.updateTrack ()

			self.builder.get_object("track-add-point-lat").set_text ('')
			self.builder.get_object("track-add-point-lon").set_text ('')
			self.builder.get_object("track-add-point-popover").hide()