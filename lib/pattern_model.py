print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, Iterable, List, Tuple, Union

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
			parentpath: str=None,
			color: Tuple=None,
			center: Tuple=None,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename
		self.parentpath = parentpath
		self.color = color
		self.center = center

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
			'center': self.center,
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
			'shapeindices': _formatValueList(self.shapeindices),
			'isdefault': self.isdefault,
			'inferredfromvalue': _formatValue(self.inferredfromvalue, keepnone=True),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			shapeindices=_parseValueList(obj.get('shapeindices')),
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
			'inferredfromvalue': _formatValue(self.inferredfromvalue, keepnone=True),
			'shapeindices': _formatValueList(self.shapeindices),
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=_parseValueList(obj.get('shapeindices')),
			**excludekeys(obj, ['sequencesteps', 'shapeindices'])
		)

	@property
	def issequenced(self):
		if not self.sequencesteps:
			return False
		if len(self.sequencesteps) > 1:
			return True
		return not self.sequencesteps[0].isdefault

class BoolOpNames:
	OR = 'or'
	AND = 'and'
	aliases = {
		AND: AND,
		'&': AND,
		OR: OR,
		'|': OR,
	}

class GroupSpec(GroupInfo):
	def __init__(
			self,
			groupname,
			basedon: List[str]=None,
			boolop: str=None,
			prerotate: float=None,
			xbound: Iterable=None,
			ybound: Iterable=None,
			**attrs):
		super().__init__(groupname=groupname, **attrs)
		self.basedon = list(basedon or [])
		self.boolop = BoolOpNames.aliases.get(boolop) or boolop
		self.prerotate = prerotate
		self.xbound = list(xbound) if xbound else None
		self.ybound = list(ybound) if ybound else None

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'basedon': _formatValueList(self.basedon),
			'boolop': self.boolop,
			'prerotate': self.prerotate,
			'xbound': _formatValueList(self.xbound),
			'ybound': _formatValueList(self.ybound),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=_parseValueList(obj.get('shapeindices')),
			basedon=_parseValueList(obj.get('basedon')),
			xbound=_parseValueList(obj.get('xbound')),
			ybound=_parseValueList(obj.get('ybound')),
			**excludekeys(obj, ['sequencesteps', 'shapeindices', 'basedon', 'xbound', 'ybound'])
		)

	@property
	def ismanual(self):
		return bool(self.sequencesteps or self.shapeindices)

	@property
	def iscombination(self):
		return bool(self.basedon or self.boolop)

	@property
	def isbounded(self):
		return bool(self.xbound or self.ybound)

	def validate(self):
		types = []
		if self.ismanual:
			types.append('manual')
		if self.iscombination:
			types.append('combination')
		if self.isbounded:
			types.append('bounded')
		if len(types) > 1:
			raise Exception('Group cannot has conflicting aspects ({}): {!r}'.format(types, self))

def _parseValue(val):
	if val is None or val == '_':
		return None
	if val == '' or isinstance(val, (int, float)):
		return val
	try:
		parsed = float(val)
		if int(parsed) == parsed:
			return int(parsed)
		return parsed
	except ValueError:
		return val

def _parseValueList(val):
	if val in (None, ''):
		return []
	if isinstance(val, str):
		return [_parseValue(v) for v in val.split(' ')]
	if isinstance(val, int):
		return [val]
	if isinstance(val, (list, tuple)):
		results = []
		for part in val:
			results.append(_parseValue(part))
		return results
	raise Exception('Unsupported index list value: {!r}'.format(val))

def _formatValue(val, keepnone=False):
	if isinstance(val, str):
		return val
	if val is None and not keepnone:
		return '_'
	if isinstance(val, float) and int(val) == val:
		return str(int(val))
	return str(val)

def _formatValueList(vals):
	if not vals:
		return None
	return ' '.join([_formatValue(i) for i in vals])
