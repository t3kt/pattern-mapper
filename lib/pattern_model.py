from abc import ABC

print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, Dict, List, Optional, Tuple, Union

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
			temporary: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.grouppath = grouppath
		self.inferencetype = inferencetype
		self.inferredfromvalue = inferredfromvalue
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])
		self.temporary = temporary

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'grouppath': self.grouppath,
			'inferencetype': self.inferencetype,
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
			'shapeindices': formatValueList(self.shapeindices),
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
			'temporary': self.temporary,
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

class SequenceByTypes:
	red = 'r'
	green = 'g'
	blue = 'b'
	# alpha = 'a'
	hue = 'h'
	saturation = 's'
	value = 'v'
	# structure = 'structure'
	x = 'x'
	y = 'y'
	distance = 'distance'

	aliases = {
		'r': red, 'red': red,
		'g': green, 'green': green,
		'b': blue, 'blue': blue,
		# 'a': alpha, 'alpha': alpha,
		'h': hue, 'hue': hue,
		's': saturation, 'sat': saturation, 'saturation': saturation,
		'v': value, 'value': value,
		# 'structure': structure,
		'd': distance, 'dist': distance, 'distance': distance,
		'x': x, 'y': y,
	}

	rgb = red, green, blue
	hsv = hue, saturation, value
	xy = x, y

class SequenceBySpec(BaseDataObject):
	def __init__(
			self,
			attr: str,
			rounddigits: int=None,
			reverse: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.attr = attr
		self.rounddigits = rounddigits
		self.reverse = reverse

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'attr': self.attr,
			'rounddigits': self.rounddigits,
			'reverse': self.reverse,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		if isinstance(obj, str):
			return cls(attr=obj)
		return cls(**obj)

_ValueListSpec = Union[str, List[Union[str, float]]]

class GroupGenSpec(BaseDataObject, ABC):
	def __init__(
			self,
			groupname: str=None,
			suffixes: _ValueListSpec=None,
			sequenceby: SequenceBySpec=None,
			temporary: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.suffixes = suffixes
		self.sequenceby = sequenceby
		if temporary is None and groupname and groupname.startswith('.'):
			self.temporary = True
		else:
			self.temporary = temporary

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'suffixes': self.suffixes,
			'sequenceby': self.sequenceby.ToJsonDict() if self.sequenceby else None,
			'temporary': self.temporary,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		gentypes = []
		if _hasany(obj, 'xmin', 'xmax', 'ymin', 'ymax'):
			gentypes.append(BoxBoundGroupGenSpec)
		if _hasany(obj, 'anglemin', 'anglemax', 'distancemin', 'distancemax'):
			gentypes.append(PolarBoundGroupGenSpec)
		if 'groups' in obj and _hasany(obj, 'withgroups', 'boolop', 'permute'):
			gentypes.append(CombinationGroupGenSpec)
		if 'paths' in obj:
			gentypes.append(PathGroupGenSpec)
		if not gentypes:
			raise Exception('Unsupported group gen spec: {}'.format(obj))
		if len(gentypes) > 1:
			raise Exception('Multiple conflicting group gen types: {}'.format(gentypes))
		t = gentypes[0]
		return t._SpecFromJsonDict(obj)

	@classmethod
	def _SpecFromJsonDict(cls, obj):
		return cls(
			sequenceby=SequenceBySpec.FromJsonDict(obj.get('sequenceby')) if obj.get('sequenceby') else None,
			**excludekeys(obj, ['sequenceby']))

def _hasany(obj, *keys):
	return obj and any(k in obj for k in keys)

class PathGroupGenSpec(GroupGenSpec):
	def __init__(
			self,
			paths: _ValueListSpec=None,
			groupatdepth: int=None,
			**attrs):
		super().__init__(**attrs)
		self.paths = paths
		self.groupatdepth = groupatdepth

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'path': self.paths,
			'groupatdepth': self.groupatdepth,
		}))

class PositionalGroupGenSpec(GroupGenSpec, ABC):
	def __init__(
			self,
			prerotate: _ValueListSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.prerotate = prerotate

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'prerotate': self.prerotate,
		}))

class BoxBoundGroupGenSpec(PositionalGroupGenSpec):
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

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'xmin': self.xmin, 'xmax': self.xmax,
			'ymin': self.ymin, 'ymax': self.ymax,
		}))

class PolarBoundGroupGenSpec(PositionalGroupGenSpec):
	def __init__(
			self,
			anglemin: _ValueListSpec=None,
			anglemax: _ValueListSpec=None,
			distancemin: _ValueListSpec=None,
			distancemax: _ValueListSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.anglemin = anglemin
		self.anglemax = anglemax
		self.distancemin = distancemin
		self.distancemax = distancemax

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'anglemin': self.anglemin, 'anglemax': self.anglemax,
			'distancemin': self.distancemin, 'distancemax': self.distancemax,
		}))

class CombinationGroupGenSpec(GroupGenSpec):
	def __init__(
			self,
			groups: _ValueListSpec=None,
			withgroups: _ValueListSpec=None,
			boolop: str=None,
			permute: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.groups = groups
		self.withgroups = withgroups
		self.boolop = boolop
		self.permute = permute

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'groups': self.groups,
			'withgroups': self.withgroups,
			'boolop': self.boolop,
			'permute': self.permute,
		}))

class PatternSettings(BaseDataObject):
	def __init__(
			self,
			groups: List[GroupGenSpec]=None,
			autogroup: Optional[bool]=None,
			rescale: bool=None,
			recenter: bool=None,
			defaultshapestate: Dict[str, Any]=None,
			**attrs):
		super().__init__(**attrs)
		self.groups = list(groups or [])
		self.rescale = rescale
		self.recenter = recenter
		self.defaultshapestate = dict(defaultshapestate or {})
		self.autogroup = autogroup

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'autogroup': self.autogroup,
			'groups': GroupGenSpec.ToJsonDicts(self.groups),
			'rescale': self.rescale,
			'recenter': self.recenter,
			'defaultshapestate': cleandict(self.defaultshapestate),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			groups=GroupGenSpec.FromJsonDicts(obj.get('groups')),
			**excludekeys(obj, ['groups'])
		)
