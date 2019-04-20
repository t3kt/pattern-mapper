from abc import ABC

print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, Dict, Iterable, List, Tuple, Union

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject

try:
	from common import parseValue, parseValueList, formatValue, formatValueList
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList

class ShapeInfo(BaseDataObject):
	def __init__(
			self,
			shapeindex: int,
			shapename: str,
			shapepath: str=None,
			parentpath: str=None,
			color: Tuple=None,
			center: Tuple=None,
			shapelength: float=None,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename
		self.shapepath = shapepath
		self.parentpath = parentpath
		self.color = color
		self.center = center
		self.shapelength = shapelength

	@property
	def hsvcolor(self):
		if not self.color:
			return None
		return rgb_to_hsv(self.color[0], self.color[1], self.color[2])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'shapeindex': self.shapeindex,
			'shapename': self.shapename,
			'shapepath': self.shapepath,
			'parentpath': self.parentpath,
			'color': self.color,
			'center': self.center,
			'shapelength': self.shapelength,
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
			'shapeindices': formatValueList(self.shapeindices),
			'isdefault': self.isdefault,
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			shapeindices=parseValueList(obj.get('shapeindices')),
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
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
			'shapeindices': formatValueList(self.shapeindices),
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=parseValueList(obj.get('shapeindices')),
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
			anglebound: Iterable=None,
			distancebound: Iterable=None,
			**attrs):
		super().__init__(groupname=groupname, **attrs)
		self.basedon = list(basedon or [])
		self.boolop = BoolOpNames.aliases.get(boolop) or boolop
		self.prerotate = prerotate
		self.xbound = list(xbound) if xbound else None
		self.ybound = list(ybound) if ybound else None
		self.anglebound = list(anglebound) if anglebound else None
		self.distancebound = list(distancebound) if distancebound else None

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'basedon': formatValueList(self.basedon),
			'boolop': self.boolop,
			'prerotate': self.prerotate,
			'xbound': formatValueList(self.xbound),
			'ybound': formatValueList(self.ybound),
			'anglebound': formatValueList(self.anglebound),
			'distancebound': formatValueList(self.distancebound),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=parseValueList(obj.get('shapeindices')),
			basedon=parseValueList(obj.get('basedon')),
			xbound=parseValueList(obj.get('xbound')),
			ybound=parseValueList(obj.get('ybound')),
			anglebound=parseValueList(obj.get('anglebound')),
			distancebound=parseValueList(obj.get('distancebound')),
			**excludekeys(obj, [
				'sequencesteps', 'shapeindices',
				'basedon',
				'xbound', 'ybound',
				'anglebound', 'distancebound',
			])
		)

	@property
	def ismanual(self):
		return bool(self.sequencesteps or self.shapeindices)

	@property
	def iscombination(self):
		return bool(self.basedon or self.boolop)

	@property
	def isbounded(self):
		return bool(self.xbound or self.ybound or self.anglebound or self.distancebound)

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

_ValueListSpec = Union[str, List[Union[str, float]]]

class GroupGenSpec(BaseDataObject, ABC):
	def __init__(
			self,
			groupname=None,
			suffixes: _ValueListSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.suffixes = suffixes

class BoxBoundGroupGenSpec(GroupGenSpec):
	def __init__(
			self,
			xmin: _ValueListSpec=None,
			xmax: _ValueListSpec=None,
			ymin: _ValueListSpec=None,
			ymax: _ValueListSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.xmin = xmin
		self.xmax = xmax
		self.ymin = ymin
		self.ymax = ymax

class PatternSettings(BaseDataObject):
	def __init__(
			self,
			groupgens: List[GroupGenSpec]=None,
			normalizescale: bool=None,
			defaultshapestate: Dict[str, Any]=None,
			**attrs):
		super().__init__(**attrs)
		self.groupgens = list(groupgens or [])
		self.normalizescale = normalizescale
		self.defaultshapestate = dict(defaultshapestate or {})
