print('pattern_lighting.py loading...')

from typing import Dict, List, Union

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys

class LightSegment(BaseDataObject):
	def __init__(
			self,
			shape: int,
			start: float=0,
			end: float=1,
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
			return cls(int(parts[0]), float(parts[1]), float(parts[2]), int(parts[3]))
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

	@classmethod
	def Parse(cls, val: Union[str, Dict, List[Union[str, Dict]]]):
		if isinstance(val, str):
			return cls(segments=[LightSegment.Parse(val)])
		if isinstance(val, dict):
			return cls(segments=[LightSegment.Parse(v) for v in val.get('segments') or []])
		if isinstance(val, (list, tuple)):
			return cls(
				segments=[LightSegment.Parse(v) for v in val])
		raise Exception('Invalid light strip value: {!r}'.format(val))

class LightPattern(BaseDataObject):
	def __init__(
			self,
			strips: List[LightStrip]=None):
		super().__init__()
		self.strips = list(strips or [])

	def ToJsonDict(self):
		return {'strips': LightStrip.ToJsonDicts(self.strips)}

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			strips=[LightStrip.Parse(s) for s in (obj.get('strips') or [])])
