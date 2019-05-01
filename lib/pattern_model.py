from abc import ABC

print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, Dict, Iterable, List, Optional, Union

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys

try:
	from common import parseValue, parseValueList, formatValue, formatValueList
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList

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

class ShapeInfo(BaseDataObject):
	def __init__(
			self,
			shapeindex: int,
			shapename: str,
			shapepath: str=None,
			parentpath: str=None,
			color: Iterable=None,
			center: Iterable=None,
			shapelength: float=None,
			depthlayer: int=None,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename
		self.shapepath = shapepath
		self.parentpath = parentpath
		self.color = list(color) if color else None
		self.center = list(center) if center else None
		self.shapelength = shapelength
		self.depthlayer = depthlayer

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
			'depthlayer': self.depthlayer,
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
			depthlayer: Union[int, str]=None,
			depth: float=None,
			shapeindices: List[int]=None,
			sequencesteps: List[SequenceStep]=None,
			temporary: bool=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.grouppath = grouppath
		self.inferencetype = inferencetype
		self.inferredfromvalue = inferredfromvalue
		self.depthlayer = depthlayer
		self.depth = depth
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])
		self.temporary = temporary

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'grouppath': self.grouppath,
			'inferencetype': self.inferencetype,
			'inferredfromvalue': formatValue(self.inferredfromvalue, nonevalue=None),
			'depthlayer': self.depthlayer,
			'depth': self.depth,
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
			depthlayer: int=None,
			mergeto: str=None,
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

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'suffixes': self.suffixes,
			'sequenceby': SequenceBySpec.ToOptionalJsonDict(self.sequenceby),
			'temporary': self.temporary,
			'depthlayer': self.depthlayer,
			'mergeto': self.mergeto,
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		gentypes = []
		if _hasany(obj, 'xmin', 'xmax', 'ymin', 'ymax'):
			gentypes.append(BoxBoundGroupGenSpec)
		if _hasany(obj, 'anglemin', 'anglemax', 'distancemin', 'distancemax'):
			gentypes.append(PolarBoundGroupGenSpec)
		if 'groups' in obj:
			if obj and _hasany(obj, 'withgroups', 'boolop', 'permute'):
				gentypes.append(BooleanGroupGenSpec)
			else:
				gentypes.append(MergeGroupGenSpec)
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
			sequenceby=SequenceBySpec.FromOptionalJsonDict(obj.get('sequenceby')),
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

class DepthLayeringSpec(BaseDataObject):
	def __init__(
			self,
			mode: str=None,
			condense: Optional[bool]=None,
			layerdistance: Optional[float]=None,
			defaultlayer: Optional[int]=None):
		super().__init__()
		self.mode = mode
		self.condense = condense
		self.layerdistance = layerdistance
		self.defaultlayer = defaultlayer

	def ToJsonDict(self):
		return cleandict({
			'mode': self.mode,
			'condense': self.condense,
			'layerdistance': self.layerdistance,
			'defaultlayer': self.defaultlayer,
		})

	@classmethod
	def FromJsonDict(cls, obj):
		if isinstance(obj, str):
			return cls(mode=obj)
		return cls(**obj)

_RGBAColor = Tuple[float, float, float, float]
_UVOffset = Union[Tuple[float, float], Tuple[float, float, float]]
_XYZ = Union[Tuple[float, float], Tuple[float, float, float]]

class TransformSpec(BaseDataObject):
	def __init__(
			self,
			scale: _XYZ=None, uniformscale: float=None,
			rotate: _XYZ=None, translate: _XYZ=None, pivot: _XYZ=None,
			**attrs):
		super().__init__(**attrs)
		self.scale = scale
		self.uniformscale = uniformscale
		self.rotate = rotate
		self.translate = translate
		self.pivot = pivot

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'scale': self.scale, 'uniformscale': self.uniformscale,
			'rotate': self.rotate, 'translate': self.translate, 'pivot': self.pivot,
		}))

	def ToParamsDict(self, prefix=None, capitalize=False):
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
		), _keyTransformer(prefix, capitalize)))

def _keyTransformer(prefix=None, capitalize=False):
	def _transformer(key):
		if prefix:
			key = prefix + key
		return key.capitalize() if capitalize else key
	return _transformer

class ShapeState(BaseDataObject):
	def __init__(
			self,
			pathcolor: _RGBAColor=None,
			# pathoncolor: _RGBAColor=None,
			# pathoffcolor: _RGBAColor=None,
			# pathphase: float=None,
			# pathperiod: float=None,
			panelcolor: _RGBAColor=None,
			# panelglobaltexlevel: float=None,
			# panelglobaluvoffset: _UVOffset=None,
			# panellocaltexlevel: float=None,
			# panellocaluvoffset: _UVOffset=None,
			localtransform: TransformSpec=None,
			globaltransform: TransformSpec=None,
			**attrs):
		super().__init__(**attrs)
		self.pathcolor = pathcolor
		self.panelcolor = panelcolor
		self.localtransform = localtransform
		self.globaltransform = globaltransform

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'pathcolor': self.pathcolor,
			'panelcolor': self.panelcolor,
			'localtransform': TransformSpec.ToOptionalJsonDict(self.localtransform),
			'globaltransform': TransformSpec.ToOptionalJsonDict(self.globaltransform),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			localtransform=TransformSpec.FromOptionalJsonDict(obj.get('localtransform')),
			globaltransform=TransformSpec.FromOptionalJsonDict(obj.get('globaltransform')),
			**excludekeys(obj, ['localtransform', 'globaltransform']))

class GroupShapeState(ShapeState):
	def __init__(
			self,
			group: _ValueListSpec=None,
			pathcolor: _RGBAColor=None,
			panelcolor: _RGBAColor=None,
			localtransform: TransformSpec=None,
			globaltransform: TransformSpec=None,
			**attrs):
		super().__init__(
			pathcolor=pathcolor,
			panelcolor=panelcolor,
			localtransform=localtransform,
			globaltransform=globaltransform,
			**attrs)
		self.group = group

	def ToJsonDict(self):
		return cleandict(mergedicts(super().ToJsonDict(), {
			'group': self.group,
		}))

class PatternSettings(BaseDataObject):
	def __init__(
			self,
			groups: List[GroupGenSpec]=None,
			autogroup: Optional[bool]=None,
			depthlayering: DepthLayeringSpec=None,
			rescale: bool=None,
			recenter: bool=None,
			defaultshapestate: ShapeState=None,
			groupshapestates: List[GroupShapeState]=None,
			**attrs):
		super().__init__(**attrs)
		self.groups = list(groups or [])
		self.rescale = rescale
		self.recenter = recenter
		self.defaultshapestate = defaultshapestate
		self.groupshapestates = list(groupshapestates or [])
		self.autogroup = autogroup
		self.depthlayering = depthlayering

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'autogroup': self.autogroup,
			'groups': GroupGenSpec.ToJsonDicts(self.groups),
			'rescale': self.rescale,
			'recenter': self.recenter,
			'defaultshapestate': ShapeState.ToOptionalJsonDict(self.defaultshapestate),
			'groupshapestates': GroupShapeState.ToJsonDicts(self.groupshapestates),
			'depthlayering': DepthLayeringSpec.ToOptionalJsonDict(self.depthlayering),
		}))

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(
			groups=GroupGenSpec.FromJsonDicts(obj.get('groups')),
			depthlayering=DepthLayeringSpec.FromOptionalJsonDict(obj.get('depthlayering')),
			defaultshapestate=ShapeState.FromOptionalJsonDict(obj.get('defaultshapestate')),
			groupshapestates=GroupShapeState.FromJsonDicts(obj.get('groupshapestates')),
			**excludekeys(obj, ['groups', 'depthlayering', 'defaultshapestate', 'groupshapestates'])
		)
