print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, List, Tuple

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject

class ShapeInfo(BaseDataObject):
	def __init__(
			self,
			shapeindex: int,
			shapename: str,
			parentpath: str,
			color: Tuple,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename
		self.parentpath = parentpath
		self.color = color

	@property
	def hsvcolor(self):
		if not self.color:
			return None
		return rgb_to_hsv(self.color[0], self.color[1], self.color[2])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'shapeindex': self.shapeindex,
			'shapename': self.shapename,
			'parentpath': self.parentpath,
			'color': self.color,
		}))

class SequenceStep(BaseDataObject):
	def __init__(
			self,
			sequenceindex=0,
			shapeindices: List[int]=None,
			isdefault: bool=None,
			inferredfromvalue: Any=None,
			**attrs):
		super().__init__(**attrs)
		self.sequenceindex = sequenceindex
		self.shapeindices = list(shapeindices or [])
		self.isdefault = isdefault
		self.inferredfromvalue = inferredfromvalue

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'sequenceindex': self.sequenceindex,
			'shapeindices': _formatIndexList(self.shapeindices),
			'isdefault': self.isdefault,
			'inferredfromvalue': self.inferredfromvalue,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			shapeindices=_parseIndexList(obj.get('shapeindices')),
			**excludekeys(obj, ['shapeindices'])
		)

class GroupInfo(BaseDataObject):
	def __init__(
			self,
			groupname,
			grouppath=None,
			inferencetype: str=None,
			inferredfromvalue: Any=None,
			shapeindices: List[int]=None,
			sequencesteps: List[SequenceStep]=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.grouppath = grouppath
		self.inferencetype = inferencetype
		self.inferredfromvalue = inferredfromvalue
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'grouppath': self.grouppath,
			'inferencetype': self.inferencetype,
			'inferredfromvalue': self.inferredfromvalue,
			'shapeindices': _formatIndexList(self.shapeindices),
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=_parseIndexList(obj.get('shapeindices')),
			**excludekeys(obj, ['sequencesteps', 'shapeindices'])
		)

class BoolOpNames:
	OR = 'or'
	AND = 'and'

class GroupSpec(GroupInfo):
	def __init__(
			self,
			groupname,
			basedongroups: List[str]=None,
			boolop: str=None,
			**attrs):
		super().__init__(groupname=groupname, **attrs)
		self.basedongroups = list(basedongroups or [])
		self.boolop = boolop

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'basedongroups': self.basedongroups,
			'boolop': self.boolop,
		}))

	@property
	def ismanual(self):
		return bool(self.sequencesteps or self.shapeindices)

	@property
	def iscombination(self):
		return bool(self.basedongroups or self.boolop)

def _parseIndexList(val):
	if not val:
		return []
	if isinstance(val, str):
		return [int(v) for v in val.split(' ')]
	if isinstance(val, int):
		return [val]
	if isinstance(val, (list, tuple)):
		results = []
		for part in val:
			results += _parseIndexList(part)
		return results
	raise Exception('Unsupported index list value: {!r}'.format(val))

def _formatIndexList(indices):
	if not indices:
		return None
	return ' '.join([str(i) for i in indices])
