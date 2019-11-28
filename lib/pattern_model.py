from abc import ABC
from enum import Enum
from dataclasses import dataclass
from colorsys import rgb_to_hsv
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, setattrs, BaseDataObject2
from .common import parseValueList, formatValue, formatValueList, averagePoints, triangleCenter

print('pattern_model.py loading...')

if False:
	from ._stubs import *

class _BaseEnum(Enum):
	@classmethod
	def ByName(cls, name: str, default=None):
		if name in (None, ''):
			return default
		try:
			return cls[name]
		except KeyError:
			return default

	@classmethod
	def ByValue(cls, value: Union[str, int], default=None):
		if value in (None, ''):
			return default
		try:
			return cls(value)
		except KeyError:
			return default

# def _defaultedgetter(getdefault: Callable):
# 	attrname = getdefault.__name__
#
# 	def _getter(self):
# 		val = getattr(self, '_' + attrname)
# 		if val is None:
# 			return getdefault(self)
# 		return val
#
# 	return property(_getter)

_RGBAColor = Tuple[float, float, float, float]
_UVOffset = Union[Tuple[float, float], Tuple[float, float, float]]
_XYZ = Union[Tuple[float, float], Tuple[float, float, float], List[float]]
_ValueListSpec = Union[str, List[Union[str, float]]]

@dataclass
class ShapeInfoBase(BaseDataObject2):
	shapename: str = None
	shapepath: str = None
	parentpath: str = None
	shapelength: float = None
	points: List['PointData'] = None
	center: _XYZ = None

	def __post_init__(self):
		self.points = list(self.points or [])

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			points=PointData.FromJsonDicts(obj.get('points')),
			**excludekeys(obj, ['points']))

	def offsetPoints(self, offset: 'tdu.Vector'):
		for point in self.points:
			point.pos = list(tdu.Vector(point.pos) + offset)

	def scalePoints(self, scale: float):
		for point in self.points:
			point.pos = list(tdu.Vector(point.pos) * scale)

@dataclass
class ShapeInfo(ShapeInfoBase):
	shapeindex: int = 0
	color: _RGBAColor = None
	center: _XYZ = None
	depthlayer: int = None
	dupcount: int = None
	radius: float = None
	rotateaxis: float = None

	def __post_init__(self):
		super().__post_init__()
		self.color = list(self.color) if self.color else None
		self.center = list(self.center) if self.center else None
		self.dupcount = self.dupcount or 0

	@property
	def isduplicate(self):
		return self.dupcount == -1

	@property
	def hsvcolor(self):
		if not self.color:
			return None
		return rgb_to_hsv(self.color[0], self.color[1], self.color[2])

	@property
	def minbound(self):
		if not self.points:
			return None
		return tdu.Vector(
			min(p.pos[0] for p in self.points),
			min(p.pos[1] for p in self.points),
			min(p.pos[2] for p in self.points),
		)

	@property
	def maxbound(self):
		if not self.points:
			return None
		return tdu.Vector(
			max(p.pos[0] for p in self.points),
			max(p.pos[1] for p in self.points),
			max(p.pos[2] for p in self.points),
		)

	@property
	def _pointsWithoutOpenLoop(self) -> List['PointData']:
		if self.isopenloop:
			return self.points[:-1]
		else:
			return self.points

	def calculateCenter(self):
		self.center = averagePoints([p.pos for p in self._pointsWithoutOpenLoop])

	def calculateTriangleCenter(self):
		self.center = triangleCenter([p.pos for p in self._pointsWithoutOpenLoop])

	def calculateRadius(self):
		center = tdu.Vector(self.center)
		self.radius = max([
			tdu.Vector(p.pos).distance(center)
			for p in self.points
		])

	def isEquivalentTo(self, other: 'ShapeInfo', tolerance=0.0):
		if other is None:
			return False
		ownpts = self._pointsWithoutOpenLoop
		otherpts = other._pointsWithoutOpenLoop
		n = len(ownpts)
		if n != len(otherpts):
			return False

		# firstindex = _firstIndexWhere(otherpts, lambda p: p.isEquivalentTo(ownpts[0]))
		# if firstindex == -1:
		# 	return False
		# otherpts = deque(otherpts)
		# otherpts.rotate(firstindex)
		# for i, ownpt in enumerate(ownpts):
		# 	otherpt = otherpts[i]
		# 	if not otherpt.isEquivalentTo(ownpts[0], tolerance):
		# 		return False
		# return True
		centerdist = tdu.Vector(self.center).distance(tdu.Vector(other.center))
		if centerdist > tolerance:
			return False
		raddiff = abs(self.radius - other.radius)
		if raddiff > tolerance:
			return False
		return True

	def containsPoint(self, testpoint: 'PointData'):
		return _shapeContainsPoint(self._pointsWithoutOpenLoop, testpoint)

	@property
	def isopenloop(self):
		if len(self.points) < 4:
			return False
		return self.points[0].pos == self.points[-1].pos

	@property
	def istriangle(self):
		if len(self.points) == 3 and not self.isopenloop:
			return True
		if len(self.points) == 4 and self.isopenloop:
			return True
		return False

	def ToJsonDict(self):
		return cleandict(
			{
				'shapeindex': self.shapeindex,
				'shapename': self.shapename,
				'shapepath': self.shapepath,
				'parentpath': self.parentpath,
				'color': self.color,
				'center': self.center,
				'shapelength': self.shapelength,
				'depthlayer': self.depthlayer or None,
				'dupcount': self.dupcount or None,
				'radius': self.radius or None,
				'rotateaxis': self.rotateaxis or None,
				'points': PointData.ToJsonDicts(self.points),
			})

def _shapeContainsPoint(shapepoints: List['PointData'], testpoint: 'PointData'):
	testx, testy = testpoint.pos[0], testpoint.pos[1]
	nshapepoints = len(shapepoints)
	inside = False
	p1x, p1y = shapepoints[0].pos[0], shapepoints[0].pos[1]
	for i in range(nshapepoints + 1):
		shapepoint = shapepoints[i % nshapepoints]
		p2x, p2y = shapepoint.pos[0], shapepoint.pos[1]
		if testy > min(p1y, p2y):
			if testy <= max(p1y, p2y):
				if testx <= max(p1x, p2x):
					if p1y != p2y:
						xints = (testy - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
					else:
						xints = -99999999
					if p1x == p2x or testx <= xints:
						inside = not inside
		p1x, p1y = p2x, p2y
	return inside

@dataclass
class PathInfo(ShapeInfoBase):

	def ToJsonDict(self):
		return cleandict(
			{
				'shapename': self.shapename,
				'shapepath': self.shapepath,
				'parentpath': self.parentpath,
				'shapelength': self.shapelength,
				'center': self.center,
				'points': PointData.ToJsonDicts(self.points),
			})

@dataclass
class PointData(BaseDataObject2):
	pos: _XYZ
	absdist: float = 0
	reldist: float = 0

	def isEquivalentTo(self, other: 'PointData', tolerance=0.0):
		return other is not None and _arePositionsInRange(self.pos, other.pos, tolerance)

def _arePositionsInRange(pos1, pos2, tolerance=0.0):
	if pos1 is None or pos2 is None:
		return False
	return tdu.Vector(pos1).distance(tdu.Vector(pos2)) <= tolerance

def _firstIndexWhere(items, test):
	for i, val in enumerate(items):
		if test(val):
			return i
	return -1

@dataclass
class SequenceStep(BaseDataObject2):
	sequenceindex: int = 0
	shapeindices: List[int] = None
	isdefault: bool = None
	inferredfromvalue: Any = None

	def __post_init__(self):
		self.shapeindices = list(self.shapeindices or [])
		self.shapeindices.sort()

	def ToJsonDict(self):
		return cleandict({
			'sequenceindex': self.sequenceindex,
			'shapeindices': formatValueList(self.shapeindices),
			'isdefault': self.isdefault or None,
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
		})

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			shapeindices=parseValueList(obj.get('shapeindices')),
			**excludekeys(obj, ['shapeindices']))

@dataclass
class GroupInfo(BaseDataObject2):
	groupname: str
	grouppath: str = None
	inferencetype: str = None
	inferredfromvalue: Any = None
	depthlayer: Union[int, str] = None
	depth: float = None
	shapeindices: List[int] = None
	sequencesteps: List[SequenceStep] = None
	temporary: bool = None
	rotateaxis: float = None

	def __post_init__(self):
		self.shapeindices = list(self.shapeindices or [])
		self.shapeindices.sort()
		self.sequencesteps = list(self.sequencesteps or [])

	def ToJsonDict(self):
		return cleandict({
			'groupname': self.groupname,
			'grouppath': self.grouppath,
			'inferencetype': self.inferencetype or None,
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
			'depthlayer': self.depthlayer or None,
			'depth': self.depth or None,
			'shapeindices': formatValueList(self.shapeindices),
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
			'temporary': self.temporary or None,
			'rotateaxis': self.rotateaxis or None,
		})

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			sequencesteps=SequenceStep.FromJsonDicts(obj.get('sequencesteps')),
			shapeindices=parseValueList(obj.get('shapeindices')),
			**excludekeys(obj, ['sequencesteps', 'shapeindices']))

	@property
	def issequenced(self):
		if not self.sequencesteps:
			return False
		if len(self.sequencesteps) > 1:
			return True
		return not self.sequencesteps[0].isdefault

	def shapeSequenceIndex(self, shapeindex: int):
		for step in self.sequencesteps:
			if shapeindex in step.shapeindices:
				return step.sequenceindex
		if shapeindex in self.shapeindices:
			return 0
		return -1

	def containsShape(self, shapeindex: int):
		if shapeindex in self.shapeindices:
			return True
		for step in self.sequencesteps:
			if shapeindex in step.shapeindices:
				return True
		return False

	@property
	def allShapeIndices(self) -> Set[int]:
		allindices = set(self.shapeindices)
		for step in self.sequencesteps:
			allindices.update(step.shapeindices)
		return allindices

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

	path = 'path'

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

@dataclass
class SequenceBySpec(BaseDataObject2):
	seqtype: str
	rounddigits: int = None
	reverse: bool = None
	path: str = None

	def ToJsonDict(self):
		return cleandict({
			'seqtype': self.seqtype,
			'rounddigits': self.rounddigits,
			'reverse': self.reverse or None,
			'path': self.path,
		})

	@classmethod
	def FromJsonDict(cls, obj):
		if isinstance(obj, str):
			return cls(seqtype=obj)
		return cls(**obj)

class GroupGenSpec(BaseDataObject, ABC):
	def __init__(
			self,
			groupname: str=None,
			suffixes: _ValueListSpec=None,
			sequenceby: SequenceBySpec=None,
			temporary: bool=None,
			depthlayer: int=None,
			mergeto: str=None,
			rotateaxis: float=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.suffixes = suffixes
		self.sequenceby = sequenceby
		if temporary is None and groupname and groupname.startswith('.'):
			self.temporary = True
		else:
			self.temporary = temporary
		self.depthlayer = depthlayer
		self.mergeto = mergeto
		self.rotateaxis = rotateaxis

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'suffixes': self.suffixes,
			'sequenceby': SequenceBySpec.ToOptionalJsonDict(self.sequenceby),
			'temporary': self.temporary or None,
			'depthlayer': self.depthlayer or None,
			'mergeto': self.mergeto or None,
			'rotateaxis': self.rotateaxis or None,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		gentypes = []
		if _hasany(obj, 'steps'):
			gentypes.append(ManualGroupGenSpec)
		if _hasany(obj, 'xmin', 'xmax', 'ymin', 'ymax'):
			gentypes.append(BoxBoundGroupGenSpec)
		if _hasany(obj, 'anglemin', 'anglemax', 'distancemin', 'distancemax'):
			gentypes.append(PolarBoundGroupGenSpec)
		if 'groups' in obj:
			if obj and _hasany(obj, 'withgroups', 'boolop', 'permute'):
				gentypes.append(BooleanGroupGenSpec)
			else:
				gentypes.append(MergeGroupGenSpec)
		if 'paths' in obj or 'path' in obj:
			gentypes.append(PathGroupGenSpec)
		if not gentypes:
			raise Exception('Unsupported group gen spec: {}'.format(obj))
		if len(gentypes) > 1:
			raise Exception('Multiple conflicting group gen types: {}'.format(gentypes))
		t = gentypes[0]
		return t.SpecFromJsonDict(obj)

	@classmethod
	def SpecFromJsonDict(cls, obj):
		return cls(
			sequenceby=SequenceBySpec.FromOptionalJsonDict(obj.get('sequenceby')),
			**excludekeys(obj, ['sequenceby']))

def _hasany(obj, *keys):
	return obj and any(k in obj for k in keys)

class ManualGroupGenSpec(GroupGenSpec):
	def __init__(
			self,
			steps: Iterable[List[int]]=None,
			**attrs):
		super().__init__(**attrs)
		self.steps = list(steps or [])

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'steps': self.steps,
		}))

	@classmethod
	def SpecFromJsonDict(cls, obj):
		return cls(
			sequenceby=SequenceBySpec.FromOptionalJsonDict(obj.get('sequenceby')),
			steps=SequenceStep.FromJsonDicts(obj.get('steps')),
			**excludekeys(obj, ['sequenceby', 'steps']))

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
			'paths': self.paths,
			'groupatdepth': self.groupatdepth or None,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			paths=obj.get('paths') or obj.get('path') or [],
			**excludekeys(obj, ['paths', 'path'])
		)

class BoundMode(_BaseEnum):
	center = 0
	full = 1
	partial = 2

class PositionalGroupGenSpec(GroupGenSpec, ABC):
	def __init__(
			self,
			prerotate: _ValueListSpec=None,
			boundmode: str=None,
			**attrs):
		super().__init__(**attrs)
		self.prerotate = prerotate
		self.boundmode = BoundMode.ByName(boundmode, BoundMode.center)

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'prerotate': self.prerotate,
			'boundmode': self.boundmode.name,
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

class BooleanGroupGenSpec(GroupGenSpec):
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

class MergeGroupGenSpec(GroupGenSpec):
	def __init__(
			self,
			groups: _ValueListSpec=None,
			flatten: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.groups = groups
		self.flatten = flatten

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'groups': self.groups,
			'flatten': self.flatten,
		}))

class GroupDepthModes:
	manual = 'manual'
	flat = 'flat'
	groupnameprefix = 'groupnameprefix'

	aliases = {
		manual: manual,
		flat: flat,
		groupnameprefix: groupnameprefix, 'prefix': groupnameprefix,
	}

@dataclass
class DepthLayeringSpec(BaseDataObject2):
	mode: str = None
	condense: Optional[bool] = None
	layerdistance: Optional[float] = None
	defaultlayer: Optional[int] = None
	generategroups: Optional[bool] = None

	@classmethod
	def FromJsonDict(cls, obj):
		if isinstance(obj, str):
			return cls(mode=obj)
		return cls(**obj)

@dataclass
class DuplicateMergeSpec(BaseDataObject2):
	tolerance: Optional[float] = None
	scopes: List['DuplicateMergeScope'] = None

	@classmethod
	def FromJsonDict(cls, obj):
		if isinstance(obj, (int, float)):
			return cls(tolerance=obj)
		return cls(
			scopes=DuplicateMergeSpec.FromJsonDicts(obj.get('scopes')),
			**excludekeys(obj, ['scopes'])
		)

	def ToJsonDict(self):
		return cleandict({
			'tolerance': self.tolerance,
			'scopes': DuplicateMergeScope.ToJsonDicts(self.scopes),
		})

@dataclass
class DuplicateMergeScope(BaseDataObject2):
	groups: _ValueListSpec = None

class TransformSpec(BaseDataObject):
	def __init__(
			self,
			scale: _XYZ=None, uniformscale: float=None,
			rotate: _XYZ=None, translate: _XYZ=None, pivot: _XYZ=None,
			**attrs):
		super().__init__(**attrs)
		self.scale = tuple(scale) if scale else None
		self.uniformscale = uniformscale
		self.rotate = tuple(rotate) if rotate else None
		self.translate = tuple(translate) if translate else None
		self.pivot = tuple(pivot) if pivot else None

	@classmethod
	def DefaultTransformSpec(cls):
		return TransformSpec(
			scale=(1, 1, 1),
			uniformscale=1,
			rotate=(0, 0, 0),
			translate=(0, 0, 0),
			pivot=(0, 0, 0),
		)

	def MergedWith(self, override: 'TransformSpec'):
		if not override:
			return self.Clone()
		return TransformSpec(
			scale=override.scale or self.scale,
			uniformscale=override.uniformscale if override.uniformscale is not None else self.uniformscale,
			rotate=override.rotate or self.rotate,
			translate=override.translate or self.translate,
			pivot=override.pivot or self.pivot,
		)

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'scale': self.scale, 'uniformscale': self.uniformscale,
			'rotate': self.rotate, 'translate': self.translate, 'pivot': self.pivot,
		}))

	def ToParamsDict(self, prefix=None):
		if not prefix:
			prefix = ''
		return cleandict(transformkeys(mergedicts(
			self.scale is not None and {
				'scalex': self.scale[0],
				'scaley': self.scale[1],
				'scalez': self.scale[2] if len(self.scale) > 2 else None,
			},
			self.uniformscale is not None and {'uniformscale': self.uniformscale},
			self.rotate is not None and {
				'rotatex': self.rotate[0],
				'rotatey': self.rotate[1],
				'rotatez': self.rotate[2] if len(self.rotate) > 2 else None,
			},
			self.translate is not None and {
				'translatex': self.translate[0],
				'translatey': self.translate[1],
				'translatez': self.translate[2] if len(self.translate) > 2 else None,
			},
			self.pivot is not None and {
				'pivotx': self.pivot[0],
				'pivoty': self.pivot[1],
				'pivotz': self.pivot[2] if len(self.pivot) > 2 else None,
			}
		), lambda key: prefix + key))

	@classmethod
	def FromParamsDict(cls, obj, prefix=None):
		if not obj:
			return None
		if not prefix:
			prefix = ''
		return cls(
			scale=_TupleFromDict(
				obj,
				'{}scalex'.format(prefix).capitalize(),
				'{}scaley'.format(prefix).capitalize(),
				'{}scalez'.format(prefix).capitalize(),
				default=1
			),
			uniformscale=obj.get('uniformscale'),
			rotate=_TupleFromDict(
				obj,
				'{}rotatex'.format(prefix).capitalize(),
				'{}rotatey'.format(prefix).capitalize(),
				'{}rotatez'.format(prefix).capitalize(),
				default=0
			),
			translate=_TupleFromDict(
				obj,
				'{}translatex'.format(prefix).capitalize(),
				'{}translatey'.format(prefix).capitalize(),
				'{}translatez'.format(prefix).capitalize(),
				default=0
			),
			pivot=_TupleFromDict(
				obj,
				'{}pivotx'.format(prefix).capitalize(),
				'{}pivoty'.format(prefix).capitalize(),
				'{}pivotz'.format(prefix).capitalize(),
				default=0
			)
		)

	@classmethod
	def AllParamNames(cls, prefix: str):
		return [
			prefix + 'scalex', prefix + 'scaley', prefix + 'scalez',
			prefix + 'uniformscale',
			prefix + 'rotatex', prefix + 'rotatey', prefix + 'rotatez',
			prefix + 'translatex', prefix + 'translatey', prefix + 'translatez',
			prefix + 'pivotx', prefix + 'pivoty', prefix + 'pivotz',
		]

	@classmethod
	def CreatePars(cls, page, prefix: str, labelprefix: str, isforuv: bool=False):
		setattrs(
			page.appendXYZ(
				(prefix + 'scale').capitalize(),
				label=labelprefix + 'Scale'),
			default=1, normMin=-1, normMax=1)
		setattrs(
			page.appendFloat(
				(prefix + 'uniformscale').capitalize(),
				label=labelprefix + 'Uniform Scale'),
			default=1, normMin=0, normMax=2)
		setattrs(
			page.appendXYZ(
				(prefix + 'rotate').capitalize(),
				label=labelprefix + 'Rotate'),
			default=0, normMin=-180, normMax=180)
		setattrs(
			page.appendXYZ(
				(prefix + 'translate').capitalize(),
				label=labelprefix + 'Translate'),
			default=0, normMin=-0.5 if isforuv else -1, normMax=0.5 if isforuv else 1,
		)
		setattrs(
			page.appendXYZ(
				(prefix + 'pivot').capitalize(),
				label=labelprefix + 'Pivot'),
			default=0.5 if isforuv else 0, normMin=0 if isforuv else -1, normMax=1,
		)

def _TupleFromDict(obj: Dict[str, Any], *names: str, default=None):
	if not obj:
		return None
	vals = []
	hasany = False
	for name in names:
		val = obj.get(name)
		if val is not None:
			vals.append(val)
			hasany = True
		else:
			vals.append(default)
	return vals if hasany else None

class TexCoordMode(_BaseEnum):
	loc = 0
	glob = 1
	path = 2

_uvmodelabels = {
	TexCoordMode.loc: 'Local',
	TexCoordMode.glob: 'Global',
	TexCoordMode.path: 'Path',
}

class CompositeOp(_BaseEnum):
	add = 0
	atop = 1
	average = 2
	difference = 3
	inside = 4
	maximum = 5
	minimum = 6
	multiply = 7
	outside = 8
	over = 9
	screen = 10
	subtract = 11
	under = 12

class TextureLayer(BaseDataObject):
	def __init__(
			self,
			uvmode: str=None,
			textureindex: int=None,
			transform: TransformSpec=None,
			composite: str=None,
			alpha: float=None,
			**attrs):
		super().__init__(**attrs)
		# parse by value
		self.uvmode = TexCoordMode.ByName(uvmode, default=TexCoordMode.loc)  # type: TexCoordMode
		self.textureindex = textureindex
		self.transform = transform
		# parse by name
		self.composite = CompositeOp.ByName(composite, default=CompositeOp.over)  # type: CompositeOp
		self.alpha = alpha or 0

	@classmethod
	def DefaultTextureLayer(cls, path=False):
		return TextureLayer(
			uvmode=TexCoordMode.path.name if path else TexCoordMode.glob.name,
			textureindex=0,
			transform=TransformSpec.DefaultTransformSpec(),
			composite=CompositeOp.over.name,
			alpha=0,
		)

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'uvmode': self.uvmode.name,
			'textureindex': self.textureindex,
			'transform': TransformSpec.ToOptionalJsonDict(self.transform),
			'composite': self.composite.name,
			'alpha': self.alpha,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			transform=TransformSpec.FromOptionalJsonDict(obj.get('transform')),
			**excludekeys(obj, ['transform'])
		)

	def ToParamsDict(self, prefix=None):
		if not prefix:
			prefix = ''
		return cleandict(mergedicts(
			transformkeys({
				'uvmode': self.uvmode.value,
				'textureindex': self.textureindex,
				'composite': self.composite.value,
				'alpha': self.alpha,
			}, lambda key: prefix + key),
			self.transform and self.transform.ToParamsDict(prefix),
		))

	@classmethod
	def FromParamsDict(cls, obj, prefix=None):
		if not prefix:
			prefix = ''
		return cls(
			uvmode=obj.get(prefix + 'uvmode'),
			textureindex=obj.get(prefix + 'textureindex'),
			transform=TransformSpec.FromParamsDict(obj, prefix),
			composite=obj.get(prefix + 'composite'),
			alpha=obj.get(prefix + 'alpha'),
		)

	@classmethod
	def AllParamNames(cls, prefix: str):
		return [
			prefix + 'uvmode',
			prefix + 'textureindex',
			prefix + 'composite',
			prefix + 'alpha',
		] + TransformSpec.AllParamNames(prefix)

	@classmethod
	def CreatePars(cls, page, prefix: str, labelprefix: str):
		setattrs(
			page.appendMenu(
				(prefix + 'uvmode').capitalize(),
				label=labelprefix + 'UV Mode'),
			menuNames=[c.name for c in TexCoordMode],
			menuLabels=[_uvmodelabels[c] for c in TexCoordMode],
			default=TexCoordMode.loc.name)
		setattrs(
			page.appendMenu(
				(prefix + 'composite').capitalize(),
				label=labelprefix + 'Composite Operator'),
			menuNames=[c.name for c in CompositeOp],
			menuLabels=[c.name.capitalize() for c in CompositeOp],
			default=CompositeOp.over.name)
		setattrs(
			page.appendInt(
				(prefix + 'textureindex').capitalize(),
				label=labelprefix + 'Texture Index'),
			default=0, normMin=0, min=0, clampMin=True, normMax=1, max=1, clampMax=True)
		setattrs(
			page.appendFloat(
				(prefix + 'alpha').capitalize(),
				label=labelprefix + 'Alpha'),
			default=0, normMin=0, normMax=1)
		TransformSpec.CreatePars(page, prefix, labelprefix, isforuv=True)

class ShapeState(BaseDataObject):
	def __init__(
			self,
			group: _ValueListSpec=None,
			pathvisible: bool=None,
			panelvisible: bool=None,
			pathcolor: _RGBAColor=None,
			panelcolor: _RGBAColor=None,
			localtransform: TransformSpec=None,
			globaltransform: TransformSpec=None,
			texturelayer1: TextureLayer=None,
			texturelayer2: TextureLayer=None,
			pathtexture: TextureLayer=None,
			**attrs):
		super().__init__(**attrs)
		self.group = group
		self.pathvisible = pathvisible
		self.panelvisible = panelvisible
		self.pathcolor = tuple(pathcolor) if pathcolor else None
		self.panelcolor = tuple(panelcolor) if panelcolor else None
		self.localtransform = localtransform
		self.globaltransform = globaltransform
		self.texturelayer1 = texturelayer1
		self.texturelayer2 = texturelayer2
		self.pathtexture = pathtexture

	@classmethod
	def DefaultState(cls):
		return ShapeState(
			pathvisible=False,
			panelvisible=False,
			pathcolor=(1, 1, 1, 1),
			panelcolor=(1, 1, 1, 1),
			localtransform=TransformSpec.DefaultTransformSpec(),
			globaltransform=TransformSpec.DefaultTransformSpec(),
			texturelayer1=TextureLayer.DefaultTextureLayer(),
			texturelayer2=TextureLayer.DefaultTextureLayer(),
			pathtexture=TextureLayer.DefaultTextureLayer(path=True),
		)

	def MergedWith(self, override: 'ShapeState'):
		if not override:
			return self.Clone()
		return ShapeState(
			group=override.group or self.group,
			pathvisible=override.pathvisible if override.pathvisible is not None else self.pathvisible,
			panelvisible=override.panelvisible if override.panelvisible is not None else self.panelvisible,
			pathcolor=override.pathcolor or self.pathcolor,
			panelcolor=override.panelcolor or self.panelcolor,
			localtransform=TransformSpec.CloneFirst(override.localtransform, self.localtransform),
			globaltransform=TransformSpec.CloneFirst(override.globaltransform, self.globaltransform),
			texturelayer1=TextureLayer.CloneFirst(override.texturelayer1, self.texturelayer1),
			texturelayer2=TextureLayer.CloneFirst(override.texturelayer2, self.texturelayer2),
			pathtexture=TextureLayer.CloneFirst(override.pathtexture, self.pathtexture),
		)

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'group': self.group,
			'pathvisible': self.pathvisible,
			'panelvisible': self.panelvisible,
			'pathcolor': self.pathcolor,
			'panelcolor': self.panelcolor,
			'localtransform': TransformSpec.ToOptionalJsonDict(self.localtransform),
			'globaltransform': TransformSpec.ToOptionalJsonDict(self.globaltransform),
			'texturelayer1': TextureLayer.ToOptionalJsonDict(self.texturelayer1),
			'texturelayer2': TextureLayer.ToOptionalJsonDict(self.texturelayer2),
			'pathtexture': TextureLayer.ToOptionalJsonDict(self.pathtexture),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			group=obj.get('group'),
			localtransform=TransformSpec.FromOptionalJsonDict(obj.get('localtransform')),
			globaltransform=TransformSpec.FromOptionalJsonDict(obj.get('globaltransform')),
			texturelayer1=TextureLayer.FromOptionalJsonDict(obj.get('texturelayer1')),
			texturelayer2=TextureLayer.FromOptionalJsonDict(obj.get('texturelayer2')),
			pathtexture=TextureLayer.FromOptionalJsonDict(obj.get('pathtexture')),
			**excludekeys(obj, [
				'localtransform', 'globaltransform',
				'texturelayer1', 'texturelayer2', 'pathtexture',
			]))

	def ToParamsDict(self):
		return cleandict(mergedicts(
			self.group is not None and {'Group': self.group},
			self.pathvisible is not None and {'Pathvisible': self.pathvisible},
			self.panelvisible is not None and {'Panelvisible': self.panelvisible},
			_colorTupleToDict('Pathcolor', self.pathcolor),
			_colorTupleToDict('Panelcolor', self.panelcolor),
			self.localtransform and self.localtransform.ToParamsDict(prefix='Local'),
			self.globaltransform and self.globaltransform.ToParamsDict(prefix='Global'),
			self.texturelayer1 and self.texturelayer1.ToParamsDict(prefix='Texlayer1'),
			self.texturelayer2 and self.texturelayer2.ToParamsDict(prefix='Texlayer2'),
			self.pathtexture and self.pathtexture.ToParamsDict(prefix='Pathtex'),
		))

	@classmethod
	def FromParamsDict(cls, obj):
		return cls(
			group=obj.get('Proup'),
			pathvisible=obj.get('Pathvisible'),
			panelvisible=obj.get('Panelvisible'),
			pathcolor=_TupleFromDict(obj, 'Pathcolorr', 'Pathcolorg', 'Pathcolorb', 'Pathcolora', default=1),
			panelcolor=_TupleFromDict(obj, 'Panelcolorr', 'Panelcolorg', 'Panelcolorb', 'Panelcolora', default=1),
			localtransform=TransformSpec.FromParamsDict(obj, prefix='Local'),
			globaltransform=TransformSpec.FromParamsDict(obj, prefix='Global'),
			texturelayer1=TextureLayer.FromParamsDict(obj, prefix='Texlayer1'),
			texturelayer2=TextureLayer.FromParamsDict(obj, prefix='Texlayer2'),
			pathtexture=TextureLayer.FromParamsDict(obj, prefix='Pathtex'),
		)

	@classmethod
	def AllParamNames(cls):
		names = [
			'Group',
			'Pathvisible', 'Panelvisible',
			'Pathcolorr', 'Pathcolorg', 'Pathcolorb', 'Pathcolora',
			'Panelcolorr', 'Panelcolorg', 'Panelcolorb', 'Panelcolora',
		]
		names += TransformSpec.AllParamNames('Local')
		names += TransformSpec.AllParamNames('Global')
		names += TextureLayer.AllParamNames('Texlayer1')
		names += TextureLayer.AllParamNames('Texlayer2')
		names += TextureLayer.AllParamNames('Pathtex')
		return names

	@classmethod
	def CreatePars(cls, o):
		page = o.appendCustomPage('Group')
		page.appendStr('Group', label='Group')
		page = o.appendCustomPage('Path')
		setattrs(
			page.appendToggle('Includepathvisible', label='Include Path Visible'),
			startSection=True)
		setattrs(
			page.appendToggle('Pathvisible', label='Path Visible'),
			default=True)
		setattrs(
			page.appendToggle(
				'Includepathcolor',
				label='Include Path Color'),
			startSection=True)
		setattrs(
			page.appendRGBA(
				'Pathcolor',
				label='Path Color'),
			default=1)
		setattrs(
			page.appendToggle('Includepathtex', label='Include Path Texture'),
			startSection=True)
		TextureLayer.CreatePars(page, 'Pathtex', 'Path Texture ')
		o.par.Pathtexuvmode.default = TexCoordMode.path.name
		page = o.appendCustomPage('Panel')
		setattrs(
			page.appendToggle('Includepanelvisible', label='Include Panel Visible'),
			startSection=True)
		setattrs(
			page.appendToggle('Panelvisible', label='Panel Visible'),
			default=True)
		setattrs(
			page.appendToggle(
				'Includepanelcolor',
				label='Include Panel Color'),
			startSection=True)
		setattrs(
			page.appendRGBA(
				'Panelcolor',
				label='Panel Color'),
			default=1)
		page = o.appendCustomPage('Local Transform')
		page.appendToggle('Includelocaltransform', label='Include Local Transform')
		TransformSpec.CreatePars(page, 'Local', 'Local ')
		page = o.appendCustomPage('Global Transform')
		page.appendToggle('Includeglobaltransform', label='Include Global Transform')
		TransformSpec.CreatePars(page, 'Global', 'Global ')
		page = o.appendCustomPage('Textures 1-2')
		setattrs(
			page.appendToggle('Includetexlayer1', label='Include Texture Layer 1'),
			startSection=True)
		TextureLayer.CreatePars(page, 'Texlayer1', 'Layer 1 ')
		setattrs(
			page.appendToggle('Includetexlayer2', label='Include Texture Layer 2'),
			startSection=True)
		TextureLayer.CreatePars(page, 'Texlayer2', 'Layer 2 ')

	def __bool__(self):
		return bool(self.pathcolor or self.panelcolor or self.localtransform or self.globaltransform)

def _colorTupleToDict(prefix: str, color: _RGBAColor):
	if not color:
		return {}
	if len(color) == 3:
		return {
			prefix + 'r': color[0],
			prefix + 'g': color[1],
			prefix + 'b': color[2],
		}
	if len(color) == 4:
		return {
			prefix + 'r': color[0],
			prefix + 'g': color[1],
			prefix + 'b': color[2],
			prefix + 'a': color[3],
		}
	raise Exception('Invalid color: {!r}'.format(color))

@dataclass
class PatternStates(BaseDataObject2):
	defaultshapestate: ShapeState = None
	groupshapestates: List[ShapeState] = None

	def __post_init__(self):
		self.groupshapestates = list(self.groupshapestates or [])

	def ToJsonDict(self):
		return cleandict({
			'defaultshapestate': ShapeState.ToOptionalJsonDict(self.defaultshapestate),
			'groupshapestates': ShapeState.ToJsonDicts(self.groupshapestates),
		})

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			defaultshapestate=ShapeState.FromOptionalJsonDict(obj.get('defaultshapestate')),
			groupshapestates=ShapeState.FromOptionalJsonDict(obj.get('groupshapestates')))


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

class PatternSettings(BaseDataObject):
	def __init__(
			self,
			groups: List[GroupGenSpec]=None,
			autogroup: Optional[bool]=None,
			depthlayering: DepthLayeringSpec=None,
			rescale: bool=None,
			recenter: Union[bool, str]=None,  # str is a reference to a shapename
			fixtrianglecenters: bool=None,
			mergedups: DuplicateMergeSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.groups = list(groups or [])
		self.rescale = rescale
		self.recenter = recenter
		self.autogroup = autogroup
		self.depthlayering = depthlayering
		self.fixtrianglecenters = fixtrianglecenters
		self.mergedups = mergedups

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'autogroup': self.autogroup or None,
			'groups': GroupGenSpec.ToJsonDicts(self.groups),
			'rescale': self.rescale or None,
			'recenter': self.recenter or None,
			'depthlayering': DepthLayeringSpec.ToOptionalJsonDict(self.depthlayering),
			'fixtrianglecenters': self.fixtrianglecenters or None,
			'mergedups': DuplicateMergeSpec.ToOptionalJsonDict(self.mergedups),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			groups=GroupGenSpec.FromJsonDicts(obj.get('groups')),
			depthlayering=DepthLayeringSpec.FromOptionalJsonDict(obj.get('depthlayering')),
			mergedups=DuplicateMergeSpec.FromOptionalJsonDict(obj.get('mergedups')),
			**excludekeys(obj, ['groups', 'depthlayering', 'paths', 'mergedups'])
		)


class PatternData(BaseDataObject):
	def __init__(
			self,
			shapes: List[ShapeInfo]=None,
			paths: List[PathInfo]=None,
			groups: List[GroupInfo]=None,
			settings: PatternSettings=None,
			title: str=None,
			svgwidth: float=None,
			svgheight: float=None,
			scale: float=None,
			**attrs):
		super().__init__(**attrs)
		self.shapes = list(shapes or [])  # type: List[ShapeInfo]
		self.paths = list(paths or [])  # type: List[PathInfo]
		self.groups = []  # type: List[GroupInfo]
		self.groupsbyname = {}  # type: Dict[str, GroupInfo]
		if groups:
			for group in groups:
				self.addGroup(group)
		self.title = title
		self.settings = settings
		self.svgwidth = svgwidth
		self.svgheight = svgheight
		self.scale = scale

	def addShapes(self, shapes: Iterable[ShapeInfo]):
		self.shapes += shapes

	def addPaths(self, paths: Iterable[PathInfo]):
		self.paths += paths

	def addGroup(self, group: GroupInfo):
		self.groups.append(group)
		if group.groupname not in self.groupsbyname:
			self.groupsbyname[group.groupname] = group

	def addGroups(self, groups: List[GroupInfo]):
		for group in groups:
			self.addGroup(group)

	def getGroup(self, groupname: str):
		return self.groupsbyname.get(groupname)

	def getGroupNamesByPatterns(self, groupnamepatterns: Iterable[str]) -> List[str]:
		matchingnames = []
		allgroupnames = list(self.groupsbyname.keys())
		for pattern in groupnamepatterns:
			for name in mod.tdu.match(pattern, allgroupnames):
				if name not in matchingnames:
					matchingnames.append(name)
		return matchingnames

	def getGroupsByPatterns(self, groupnamepatterns: Iterable[str]) -> List[GroupInfo]:
		names = self.getGroupNamesByPatterns(groupnamepatterns)
		return [self.groupsbyname[name] for name in names]

	def getShapeIndicesByGroupPattern(self, groupnamepatterns: Iterable[str]) -> Set[int]:
		shapeindices = set()
		groups = self.getGroupsByPatterns(groupnamepatterns)
		for group in groups:
			shapeindices.update(group.allShapeIndices)
		return shapeindices

	def getShapesByIndices(self, shapeindices: Iterable[int]) -> List[ShapeInfo]:
		if not shapeindices:
			return []
		shapeindices = set(shapeindices)
		return [
			shape
			for shape in self.shapes
			if shape.shapeindex in shapeindices
		]

	def getShapeByIndex(self, shapeindex: int):
		for shape in self.shapes:
			if shape.shapeindex == shapeindex:
				return shape

	def getShapeByName(self, shapename: str):
		if not shapename:
			return None
		for shape in self.shapes:
			if shape.shapename == shapename:
				return shape
		return None

	def removeTemporaryGroups(self):
		toremove = [group for group in self.groups if group.temporary]
		for group in toremove:
			self.groups.remove(group)
			if group.groupname and group.groupname in self.groupsbyname:
				del self.groupsbyname[group.groupname]

	def __repr__(self):
		return 'PatternData({} shapes, {} groups)'.format(len(self.shapes), len(self.groups))

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'shapes': ShapeInfo.ToJsonDicts(
				sorted(self.shapes, key=lambda s: s.shapeindex)),
			'paths': PathInfo.ToJsonDicts(
				sorted(self.paths, key=lambda p: p.shapepath)),
			'groups': GroupInfo.ToJsonDicts(
				sorted(self.groups, key=lambda g: g.groupname)),
			'title': self.title,
			'settings': PatternSettings.ToOptionalJsonDict(self.settings),
			'svgwidth': formatValue(self.svgwidth, nonevalue=None),
			'svgheight': formatValue(self.svgheight, nonevalue=None),
			'scale': formatValue(self.scale, nonevalue=None),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			shapes=ShapeInfo.FromJsonDicts(obj.get('shapes')),
			paths=PathInfo.FromJsonDicts(obj.get('paths')),
			groups=GroupInfo.FromJsonDicts(obj.get('groups')),
			settings=PatternSettings.FromOptionalJsonDict(obj.get('settings')),
			**excludekeys(obj, ['shapes', 'groups', 'settings', 'paths'])
		)
