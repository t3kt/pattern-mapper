print('pattern_groups.py loading...')

if False:
	from ._stubs import *

from pattern_model import *
from abc import ABC

try:
	from common import LoggableSubComponent, cartesiantopolar
except ImportError:
	from .common import LoggableSubComponent, cartesiantopolar

try:
	from common import parseValue, formatValue, ValueRange, ValueSequence, ValueRangeSequence
except ImportError:
	from .common import parseValue, formatValue, ValueRange, ValueSequence, ValueRangeSequence


class _ShapePredicate:
	def test(self, shape: ShapeInfo, index: int): raise NotImplementedError()

	def filter(self, shapes: List[ShapeInfo], index: int):
		return [s for s in shapes if self.test(s, index)]

	def __len__(self):
		return 1

def _parseRotateAsMatrix(val):
	val = parseValue(val)
	xform = tdu.Matrix()
	if val:
		xform.rotate(0, 0, val, pivot=(0, 0, 0))
	return xform

class _PositionalPredicate(_ShapePredicate, ABC):
	def __init__(self, groupspec: PositionalGroupSpec):
		self.prerotates = ValueSequence.FromSpec(
			groupspec.prerotate,
			parse=_parseRotateAsMatrix,
			cyclic=True)

	def test(self, shape: ShapeInfo, index: int):
		pos = tdu.Position(shape.center)
		xform = self.prerotates[index]
		if xform is not None:
			pos *= xform
		return self._testPosition(pos, index)

	def _testPosition(self, pos: tdu.Position, index: int):
		raise NotImplementedError()

class _CartesianPredicate(_PositionalPredicate):
	def __init__(self, groupspec: BoxBoundGroupGenSpec):
		super().__init__(groupspec)
		self.xranges = ValueRangeSequence.FromSpecs(
			groupspec.xmin, groupspec.xmax,
			cyclic=True, parse=float)
		self.yranges = ValueRangeSequence.FromSpecs(
			groupspec.ymin, groupspec.ymax,
			cyclic=True, parse=float)

	def __repr__(self):
		desc = '(x: {} y: {}'.format(self.xranges, self.yranges)
		if self.prerotates:
			desc += ' rotate: {}'.format(self.prerotates)
		return desc + ')'

	def __len__(self):
		return max(len(self.xranges), len(self.yranges))

	def _testPosition(self, pos: tdu.Position, index: int):
		return self.xranges.contains(pos.x, index) and self.yranges.contains(pos.y, index)

class _PolarPredicate(_PositionalPredicate):
	def __init__(self, groupspec: PolarBoundGroupGenSpec):
		super().__init__(groupspec)
		self.angleranges = ValueRangeSequence.FromSpecs(
			groupspec.anglemin, groupspec.anglemax,
			cyclic=True, parse=float)
		self.distanceranges = ValueRangeSequence.FromSpecs(
			groupspec.distancemin, groupspec.distancemax,
			cyclic=True, parse=float)

	def __repr__(self):
		desc = '(angle: {} dist: {}'.format(self.angleranges, self.distanceranges)
		if self.prerotates:
			desc += ' rotate: {}'.format(self.prerotates)
		return desc + ')'

	def __len__(self):
		return max(len(self.angleranges), len(self.distanceranges))

	def _testPosition(self, pos: tdu.Position, index: int):
		dist, angle = cartesiantopolar(pos.x, pos.y)
		return self.distanceranges.contains(dist, index) and self.angleranges.contains(angle, index)

# class _MultiPredicate(_ShapePredicate):
# 	def __init__(self, *predicates: _ShapePredicate):
# 		self.predicates = [p for p in predicates if p is not None]
#
# 	def test(self, shape: ShapeInfo, index: int):
# 		if not self.predicates:
# 			return True
# 		return any([p.test(shape, index) for p in self.predicates])
#
# 	def __repr__(self):
# 		return ' '.join([repr(p) for p in self.predicates])

class GroupGenContext:
	def __init__(self):
		self.groups = []  # type: List[GroupInfo]
		self.groupsbyname = {}  # type: Dict[str, GroupInfo]

	def addGroup(self, group: GroupInfo):
		self.groups.append(group)
		if group.groupname not in self.groupsbyname:
			self.groupsbyname[group.groupname] = group

	def getGroup(self, groupname: str):
		return self.groupsbyname.get(groupname)

	def getGroupsWithShape(self, shapeindex: int):
		return [
			group
			for group in self.groups
			if shapeindex in group.shapeindices
		]

class GroupGenerator(ABC):
	def __init__(self, groupspec: GroupGenSpec):
		# self.basedongroups = ValueSequence(groupspec.basedon, cyclic=True)
		self.basename = groupspec.groupname
		if not groupspec.suffixes:
			self.suffixes = None
		else:
			self.suffixes = ValueSequence(groupspec.suffixes, cyclic=False, backup=lambda i: i)

	def _getName(self, index: int, issolo=False):
		name = self.basename
		if self.suffixes is None:
			if index == 0 and issolo:
				return name
			else:
				suffix = 0
		else:
			suffix = self.suffixes[index]
		return self.basename + str(suffix)

	def generateGroups(self, shapes: List[ShapeInfo], context: GroupGenContext) -> List[GroupSpec]:
		raise NotImplementedError()

	@classmethod
	def FromSpec(cls, groupspec: GroupGenSpec):
		if isinstance(groupspec, BoxBoundGroupGenSpec):
			return _BoxBoundGroupGenerator(groupspec)
		elif isinstance(groupspec, PolarBoundGroupGenSpec):
			return _PolarBoundGroupGenerator(groupspec)
		elif isinstance(groupspec, CombinationGroupGenSpec):
			return _CombinationGroupGenerator(groupspec)
		else:
			raise Exception('Unsupported group gen spec: {} (type: {})'.format(
				groupspec, type(groupspec)))

class _PredicateGroupGenerator(GroupGenerator):
	def __init__(self, groupspec: GroupGenSpec, predicate: _ShapePredicate):
		super().__init__(groupspec)
		self.predicate = predicate

	def generateGroups(self, shapes: List[ShapeInfo], context: GroupGenContext):
		groups = []
		n = len(self.predicate)
		for i in range(n):
			groupshapes = self.predicate.filter(shapes, i)
			if not groupshapes:
				continue
			groupshapeindices = [s.shapeindex for s in groupshapes]
			group = GroupInfo(
				groupname=self._getName(i),
				shapeindices=groupshapeindices,
				sequencesteps=[SequenceStep(shapeindices=groupshapeindices,isdefault=True)])
			groups.append(group)
		if len(groups) == 1 and self.suffixes is None:
			groups[0].groupname = self._getName(0, issolo=True)
		return groups

class _BoxBoundGroupGenerator(_PredicateGroupGenerator):
	def __init__(self, groupspec: BoxBoundGroupGenSpec):
		super().__init__(
			groupspec,
			predicate=_CartesianPredicate(groupspec),
		)

class _PolarBoundGroupGenerator(_PredicateGroupGenerator):
	def __init__(self, groupspec: PolarBoundGroupGenSpec):
		super().__init__(
			groupspec,
			predicate=_PolarPredicate(groupspec),
		)

class _CombinationGroupGenerator(GroupGenerator):
	def __init__(self, groupspec: CombinationGroupGenSpec):
		super().__init__(groupspec)
		self.groups1 = ValueSequence(groupspec.groups, cyclic=True)
		if groupspec.withgroups is None:
			self.groups2 = self.groups1
		else:
			self.groups2 = ValueSequence(groupspec.withgroups, cyclic=True)
		self.combinator = groupspec.combine

	def generateGroups(self, shapes: List[ShapeInfo], context: GroupGenContext):
		raise NotImplementedError()
