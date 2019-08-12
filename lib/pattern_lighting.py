print('pattern_lighting.py loading...')

from typing import Dict, List, Union
import json

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod

class LightSegment(BaseDataObject):
	def __init__(
			self,
			shape: int,
			start: int=0,
			end: int=1,
			count: int=3):
		super().__init__()
		self.shape = shape
		self.start = start
		self.end = end
		self.count = count

	def ToJsonDict(self):
		return {'shape': self.shape, 'start': self.start, 'end': self.end, 'count': self.count}

	def __str__(self):
		return '{},{},{},{}'.format(self.shape, self.start, self.end, self.count)

	@classmethod
	def Parse(cls, val: Union[str, Dict]):
		if isinstance(val, str):
			parts = val.split(',')
			return cls(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]) if len(parts) > 3 else 3)
		if isinstance(val, dict):
			return cls(**val)
		raise Exception('Invalid light segment value: {!r}'.format(val))

class LightStrip(BaseDataObject):
	def __init__(
			self,
			segments: Union[str, List[LightSegment]]=None):
		super().__init__()
		if isinstance(segments, str):
			segstrs = segments.split(' ')
			self.segments = [LightSegment.Parse(s) for s in segstrs]
		else:
			self.segments = list(segments or [])

	def ToJsonDict(self):
		return {'segments': [str(s) for s in self.segments]}

	@property
	def lightcount(self):
		return sum(s.count for s in self.segments)

	@classmethod
	def Parse(cls, val: Union[str, Dict, List[Union[str, Dict]]]):
		if isinstance(val, str):
			parts = val.split(' ')
			return cls(segments=[LightSegment.Parse(v) for v in parts])
		if isinstance(val, dict):
			return cls(segments=[LightSegment.Parse(v) for v in val.get('segments') or []])
		if isinstance(val, (list, tuple)):
			return cls(
				segments=[LightSegment.Parse(v) for v in val])
		raise Exception('Invalid light strip value: {!r}'.format(val))

	def __str__(self):
		return ' '.join(str(segment) for segment in self.segments)

class LightPattern(BaseDataObject):
	def __init__(
			self,
			strips: List[LightStrip]=None):
		super().__init__()
		self.strips = list(strips or [])

	def ToJsonDict(self):
		return {'strips': LightStrip.ToJsonDicts(self.strips)}

	@property
	def maxstriplength(self):
		return max(s.lightcount for s in self.strips)

	@property
	def stripcount(self):
		return len(self.strips)

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(strips=[LightStrip.Parse(s) for s in (obj.get('strips') or [])])

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
		):
		self.strip = strip
		self.segment = segment
		self.indexinseg = indexinseg
		self.indexinstrip = indexinstrip
		self.ratioinseg = ratioinseg
		self.shape = shape
		self.vertex = vertex
