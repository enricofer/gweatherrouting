# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
# Copyright (C) 2012 Riccardo Apolloni
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
import LatLon23
import math
import os
import json
from geojson_utils import point_in_polygon


this_dir, this_fn = os.path.split (__file__)
COUNTRIES = json.load (open (this_dir + '/../data/countries.geojson', 'r'))
COUNTRY_SHAPES = []

def extractCoordinates(coord):
	c = []
	for x in coord:
		if type(x[0]) == float:
			return coord 
		else:
			for xx in extractCoordinates(x):
				c.append(xx)
	return c

for feature in COUNTRIES['features']:
	# Calculate bbox for every feature
	c = extractCoordinates(feature["geometry"]["coordinates"])
	c2 = [x[0] for x in c] 
	c1 = [x[1] for x in c]

	bbox = [[min(c1),min(c2)],[max(c1),max(c2)]]

	feature['properties']['bbox'] = bbox

	COUNTRY_SHAPES.append(feature)


def point_in_bbox(bbox, lat, lon):
	if lat >= bbox[0][0] and lat <= bbox[1][0] and lon >= bbox[0][1] and lon <= bbox[1][1]:
		return True
	return False


# def bbox_inside(bbox1, bbox2):
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[0][0], bbox1[0][1]]}, {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[1][0], bbox1[1][1]]}, {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[2][0], bbox1[2][1]]}, {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True
# 	if point_in_polygon({"type": "Point", "coordinates": [bbox1[3][0], bbox1[3][1]]}, {"type": "Polygon", "coordinates": [bbox2]}):
# 		return True

# 	return False

# # Return a list of country geometry that intersecate a bbox
# def countriesInBBox(bbox):
# 	ilist = []

# 	for feature in COUNTRY_SHAPES:
# 		if bbox_inside(bbox, feature['properties']['bbox'][0]):
# 			ilist.append(feature)
# 		elif bbox_inside(feature['properties']['bbox'][0], bbox):
# 			ilist.append(feature)

# 	return ilist


# Return true if the given point is inside a country
def pointInCountry (lat, lon):
	for feature in COUNTRY_SHAPES:
		if point_in_bbox(feature['properties']['bbox'], lat, lon):
			if point_in_polygon({"type": "Point", "coordinates": [lon, lat]}, feature['geometry']):
				return True

	return False


def uniqueName(name, collection):
	names = []
	for x in collection:
		names.append(x.name)
	if name in names:
		for i in range(1,1000):
			nname = name + '-' + str(i)
			if not (nname in names):
				return nname
	return name

EARTH_RADIUS=60.0*360/(2*math.pi)#nm


def ortodromic2 (lat1, lon1, lat2, lon2):
	p1 = math.radians (lat1)
	p2 = math.radians (lat2)
	dp = math.radians (lat2-lat1)
	dp2 = math.radians (lon2-lon1)

	a = math.sin (dp/2) * math.sin (dp2/2) + math.cos (p1) * math.cos (p2) * math.sin (dp2/2) * math.sin (dp2/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	return (EARTH_RADIUS * c, a)

def ortodromic (latA,lonA,latB,lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))

	return (p1.distance (p2), math.radians (p1.heading_initial(p2)))

def lossodromic (latA,lonA,latB,lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))

	return (p1.distance (p2, ellipse = 'sphere'), math.radians (p1.heading_initial(p2)))

def pointDistance (latA, lonA, latB, lonB):
	p1 = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	p2 = LatLon23.LatLon(LatLon23.Latitude(latB), LatLon23.Longitude(lonB))
	return p1.distance (p2)
	

def routagePointDistance (latA,lonA,Distanza,Rotta):
	p = LatLon23.LatLon(LatLon23.Latitude(latA), LatLon23.Longitude(lonA))
	of = p.offset (math.degrees (Rotta), Distanza).to_string('D')
	return (float (of[0]), float (of[1]))


def reduce360 (alfa):
	if math.isnan (alfa):
		return 0.0
		
	n=int(alfa*0.5/math.pi)
	n=math.copysign(n,1)
	if alfa>2.0*math.pi:
		alfa=alfa-n*2.0*math.pi
	if alfa<0:
		alfa=(n+1)*2.0*math.pi+alfa
	if alfa>2.0*math.pi or alfa<0:
		return 0.0
	return alfa

def reduce180 (alfa):
	if alfa>math.pi:
		alfa=alfa-2*math.pi
	if alfa<-math.pi:
		alfa=2*math.pi+alfa
	if alfa>math.pi or alfa<-math.pi:
		return 0.0
	return alfa


class DictCache(dict):
	def __init__(self, max_entries=50):
		self.entries = []
		self.max_entries = max_entries

	def __setitem__(self, key, value):
		super(DictCache, self).__setitem__(key, value)
		self.__dict__.update({key: value})
		self.entries.append(key)
		
		if len(self.entries) > self.max_entries:
			td = self.entries[0]
			self.entries = self.entries[1::]

	def __delitem__(self, key):
		super(DictCache, self).__delitem__(key)
		del self.__dict__[key]
		self.entries.remove(key)

	