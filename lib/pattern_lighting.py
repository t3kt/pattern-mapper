from math import ceil, floor

print('pattern_lighting.py loading...')

from typing import Dict, List, Union
import json

if False:
	from ._stubs import *

TDF = op.TDModules.mod.TDFunctions

if False:
	import TDFunctions as TDF

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod

from pattern_model import LightStrip, LightPattern

class LightingLoader(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		TDF.createProperty(self, 'LightPattern', value=LightPattern(), dependable=True)
		if False:
			self.LightPattern = None  # type: LightPattern
		self.LoadPattern()

	@loggedmethod
	def LoadPattern(self):
		patternjson = self.op('lighting_json').text
		patternobj = json.loads(patternjson) if patternjson else {}
		self.LightPattern = LightPattern.FromJsonDict(patternobj)
		self.BuildStripTable(self.op('set_strip_table'))
		self.BuildSegmentTable(self.op('set_segment_table'))
		self.BuildLightValues(self.op('set_light_vals'))
		self.BuildLightMapValues(self.op('set_light_map_vals'))

	@loggedmethod
	def BuildStripTable(self, dat):
		dat.clear()
		dat.appendRow([
			'stripindex',
			'segmentcount',
			'lightcount',
			'segments',
		])
		if not self.LightPattern:
			return
		for stripindex, strip in enumerate(self.LightPattern.strips):
			dat.appendRow([
				stripindex,
				len(strip.segments),
				strip.lightcount,
				str(strip)
			])

	@loggedmethod
	def BuildSegmentTable(self, dat):
		dat.clear()
		dat.appendRow([
			'stripindex',
			'segmentindex',
			'count',
			'shape',
			'start',
			'end',
		])
		if not self.LightPattern:
			return
		for stripindex, strip in enumerate(self.LightPattern.strips):
			for segindex, segment in enumerate(strip.segments):
				dat.appendRow([
					stripindex,
					segindex,
					segment.count,
					segment.shape,
					segment.start,
					segment.end,
				])

	def _GetLightPatternMap(self):
		return _LightPatternMap(self.LightPattern)

	@loggedmethod
	def BuildLightValues(self, chop):
		chop.clear()
		chop.appendChan('strip')
		chop.appendChan('segment')
		chop.appendChan('indexinsegment')
		chop.appendChan('ratioinsegment')
		chop.appendChan('indexinstrip')
		chop.appendChan('shape')
		chop.appendChan('vertex')
		if not self.LightPattern:
			chop.numSamples = 0
			return
		lightmap = self._GetLightPatternMap()
		# self._LogEvent('light objs: {!r}'.format(lightobjs))
		chop.numSamples = len(lightmap.lights)
		for light in lightmap.lights:
			chop['strip'][light.lightindex] = light.strip
			chop['segment'][light.lightindex] = light.segment
			chop['indexinsegment'][light.lightindex] = light.indexinseg
			chop['ratioinsegment'][light.lightindex] = light.ratioinseg
			chop['indexinstrip'][light.lightindex] = light.indexinstrip
			chop['shape'][light.lightindex] = light.shape
			chop['vertex'][light.lightindex] = light.vertex

	@loggedmethod
	def BuildLightMapValues(self, chop):
		chop.clear()
		if not self.LightPattern:
			chop.numSamples = 0
			return
		n = self.LightPattern.maxstriplength
		chop.numSamples = n
		lightmap = self._GetLightPatternMap()
		for stripindex, striplights in enumerate(lightmap.lightsbystrip):
			lightindexchan = chop.appendChan('lightindex{}'.format(stripindex))
			segmentchan = chop.appendChan('segment{}'.format(stripindex))
			shapechan = chop.appendChan('shape{}'.format(stripindex))
			vertexchan = chop.appendChan('vertex{}'.format(stripindex))
			for i in range(n):
				if i >= len(striplights):
					lightindexchan[i] = -1
					segmentchan[i] = -1
					shapechan[i] = -1
					vertexchan[i] = -1
				else:
					lightobj = striplights[i]
					lightindexchan[i] = lightobj.lightindex
					lightobj = striplights[i]
					segmentchan[i] = lightobj.segment
					vertexchan[i] = lightobj.vertex

	@loggedmethod
	def BuildLightCoords(self, chop, lightattrschop, shapepanelsop):
		chop.clear()
		for name in [
			'tx', 'ty', 'tz',
			'pathu', 'pathv', 'pathw',
			'faceu', 'facev', 'facew',
			'globalu', 'globalv', 'globalw',
		]:
			chop.appendChan(name)
		n = lightattrschop.numSamples
		chop.numSamples = n
		primsbyindex = {
			int(prim.shapeIndex[0]): prim
			for prim in shapepanelsop.prims
			if prim.shapeIndex[0] >= 0
		}
		for i in range(n):
			shapeindex = lightattrschop['shape'][i]
			poly = primsbyindex.get(shapeindex)
			if poly is None:
				pos, pathuv, faceuv, globaluv = _vertcoords(None)
			else:
				vertex = lightattrschop['vertex'][i]
				vert1 = poly[int(ceil(vertex))]
				pos, pathuv, faceuv, globaluv = _vertcoords(vert1)
				if int(vertex) < vertex:
					vert2 = poly[int(floor(vertex))]
					pos2, pathuv2, faceuv2, globaluv2 = _vertcoords(vert2)
					ratio = vertex - int(vertex)
					pos = _lerptuple(ratio, pos, pos2)
					pathuv = _lerptuple(ratio, pathuv, pathuv2)
				# 	faceuv = _lerptuple(ratio, faceuv, faceuv2)
				# 	globaluv = _lerptuple(ratio, globaluv, globaluv2)
			chop['tx'][i] = pos[0]
			chop['ty'][i] = pos[1]
			chop['tz'][i] = pos[2]
			chop['pathu'][i] = pathuv[0]
			chop['pathv'][i] = pathuv[1]
			chop['pathw'][i] = pathuv[2]
			chop['faceu'][i] = faceuv[0]
			chop['facev'][i] = faceuv[1]
			chop['facew'][i] = faceuv[2]
			chop['globalu'][i] = globaluv[0]
			chop['globalv'][i] = globaluv[1]
			chop['globalw'][i] = globaluv[2]

def _vertcoords(vertex):
	if vertex is None:
		return (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)
	# i don't think slices work properly for vertex attr values.. hence the manual indexing
	pos = vertex.point.x, vertex.point.y, vertex.point.z
	pathuv = vertex.uv[0], vertex.uv[1], vertex.uv[2]
	faceuv = vertex.uv[3], vertex.uv[4], vertex.uv[5]
	globaluv = vertex.uv[6], vertex.uv[7], vertex.uv[8]
	return pos, pathuv, faceuv, globaluv

def _lerp(x, low, high):
	# or could just use tdu.remap()
	return low + (high - low) * x

def _lerptuple(x, lows, highs):
	return tuple(_lerp(x, low, highs[i]) for i, low in enumerate(lows))

def _lightInfosFromStrip(stripindex: int, strip: LightStrip):
	lights = []
	indexinstrip = 0
	for segindex, segment in enumerate(strip.segments):
		for light in range(segment.count):
			lights.append(_LightInfo(
				strip=stripindex,
				segment=segindex,
				indexinseg=light,
				indexinstrip=indexinstrip,
				ratioinseg=light / (segment.count - 1),
				shape=segment.shape,
				vertex=tdu.remap(light, 0, segment.count - 1, segment.start, segment.end),
			))
			indexinstrip += 1
	return lights

def _lightInfosFromPattern(lightpattern: LightPattern):
	lights = []
	for stripindex, strip in enumerate(lightpattern.strips):
		lights += _lightInfosFromStrip(stripindex, strip)
	return lights

class _LightInfo(BaseDataObject):
	def __init__(
			self,
			strip: int,
			segment: int,
			indexinseg: int,
			indexinstrip: int,
			ratioinseg: float,
			shape: int,
			vertex: float,
			lightindex: int = None
		):
		self.strip = strip
		self.segment = segment
		self.indexinseg = indexinseg
		self.indexinstrip = indexinstrip
		self.ratioinseg = ratioinseg
		self.shape = shape
		self.vertex = vertex
		self.lightindex = lightindex
		super().__init__()

	def ToJsonDict(self):
		return cleandict({
			'strip': self.strip,
			'segment': self.segment,
			'indexinseg': self.indexinseg,
			'indexinstrip': self.indexinstrip,
			'ratioinseg': self.ratioinseg,
			'shape': self.shape,
			'vertex': self.vertex,
			'lightindex': self.lightindex,
		})

class _LightPatternMap:
	def __init__(self, lightpattern: LightPattern):
		self.lightpattern = lightpattern or LightPattern()
		self.lights = []  # type: List[_LightInfo]
		self.lightsbystrip = []  # type: List[List[_LightInfo]]
		self.lightsbystrip = [
			[] for _ in self.lightpattern.strips
		]
		if lightpattern.strips:
			lightindex = 0
			for stripindex, strip in enumerate(lightpattern.strips):
				indexinstrip = 0
				for segindex, segment in enumerate(strip.segments):
					for indexinseg in range(segment.count):
						light = _LightInfo(
							strip=stripindex,
							segment=segindex,
							indexinseg=indexinseg,
							indexinstrip=indexinstrip,
							ratioinseg=indexinseg / (segment.count - 1),
							shape=segment.shape,
							# TODO: better handling of wrapping around from the last vertex to the first
							vertex=tdu.remap(indexinseg, 0, segment.count - 1, segment.start, segment.end),
							lightindex=lightindex)
						indexinstrip += 1
						lightindex += 1
						self.lightsbystrip[stripindex].append(light)
						self.lights.append(light)
