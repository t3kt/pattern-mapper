from math import ceil, floor

print('pattern_lighting.py loading...')

from typing import Dict, List, Union
import json

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod

from pattern_model import LightStrip, LightPattern, LightSegment

class LightingLoader(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.lightpattern = LightPattern()

	@loggedmethod
	def LoadPattern(self):
		patternjson = self.op('lighting_json').text
		patternobj = json.loads(patternjson) if patternjson else {}
		self.lightpattern = LightPattern.FromJsonDict(patternobj)
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
		if not self.lightpattern:
			return
		for stripindex, strip in enumerate(self.lightpattern.strips):
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
		if not self.lightpattern:
			return
		for stripindex, strip in enumerate(self.lightpattern.strips):
			for segindex, segment in enumerate(strip.segments):
				dat.appendRow([
					stripindex,
					segindex,
					segment.count,
					segment.shape,
					segment.start,
					segment.end,
				])

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
		if not self.lightpattern:
			chop.numSamples = 0
			return
		lightobjs = _lightInfosFromPattern(self.lightpattern)
		# self._LogEvent('light objs: {!r}'.format(lightobjs))
		chop.numSamples = len(lightobjs)
		for lightindex, light in enumerate(lightobjs):
			chop['strip'][lightindex] = light.strip
			chop['segment'][lightindex] = light.segment
			chop['indexinsegment'][lightindex] = light.indexinseg
			chop['ratioinsegment'][lightindex] = light.ratioinseg
			chop['indexinstrip'][lightindex] = light.indexinstrip
			chop['shape'][lightindex] = light.shape
			chop['vertex'][lightindex] = light.vertex
		chop.cook(force=True)  # not sure why this is needed but it seems to be at the moment

	@loggedmethod
	def BuildLightMapValues(self, chop):
		chop.clear()
		if not self.lightpattern:
			chop.numSamples = 0
			return
		n = self.lightpattern.maxstriplength
		chop.numSamples = n
		for stripindex, strip in enumerate(self.lightpattern.strips):
			lightobjs = _lightInfosFromStrip(stripindex, strip)
			segmentchan = chop.appendChan('segment{}'.format(stripindex))
			indexinstripchan = chop.appendChan('indexinstrip{}'.format(stripindex))
			shapechan = chop.appendChan('shape{}'.format(stripindex))
			vertexchan = chop.appendChan('vertex{}'.format(stripindex))
			for i in range(n):
				if i >= len(lightobjs):
					segmentchan[i] = -1
					indexinstripchan[i] = -1
					shapechan[i] = -1
					vertexchan[i] = -1
				else:
					lightobj = lightobjs[i]
					segmentchan[i] = lightobj.segment
					indexinstripchan[i] = lightobj.indexinstrip
					vertexchan[i] = lightobj.vertex
		chop.cook(force=True)  # not sure why this is needed but it seems to be at the moment

	@loggedmethod
	def BuildLightUVs(self, chop, lightattrschop, shapepanelsop):
		chop.clear()
		for name in [
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
				pathuv, faceuv, globaluv = _vertuvs(None)
			else:
				vertex = lightattrschop['vertex'][i]
				vert1 = poly[int(ceil(vertex))]
				pathuv, faceuv, globaluv = _vertuvs(vert1)
				if int(vertex) < vertex:
					vert2 = poly[int(floor(vertex))]
					pathuv2, faceuv2, globaluv2 = _vertuvs(vert2)
					ratio = vertex - int(vertex)
					pathuv = _lerptuple(ratio, pathuv, pathuv2)
				# 	faceuv = _lerptuple(ratio, faceuv, faceuv2)
				# 	globaluv = _lerptuple(ratio, globaluv, globaluv2)
			chop['pathu'][i] = pathuv[0]
			chop['pathv'][i] = pathuv[1]
			chop['pathw'][i] = pathuv[2]
			chop['faceu'][i] = faceuv[0]
			chop['facev'][i] = faceuv[1]
			chop['facew'][i] = faceuv[2]
			chop['globalu'][i] = globaluv[0]
			chop['globalv'][i] = globaluv[1]
			chop['globalw'][i] = globaluv[2]

def _vertuvs(vertex):
	if vertex is None:
		return (0, 0, 0), (0, 0, 0), (0, 0, 0)
	# i don't think slices work properly for vertex attr values.. hence the manual indexing
	pathuv = vertex.uv[0], vertex.uv[1], vertex.uv[2]
	faceuv = vertex.uv[3], vertex.uv[4], vertex.uv[5]
	globaluv = vertex.uv[6], vertex.uv[7], vertex.uv[8]
	return pathuv, faceuv, globaluv

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

class _LightInfo:
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

class _LightPatternMap:
	def __init__(self, lightpattern: LightPattern):
		self.lightpattern = lightpattern
		self.lights = []  # type: List[_LightInfo]
		pass
