print('pattern_groups.py loading...')

if False:
	from ._stubs import *

from pattern_model import *
from abc import ABC
from typing import Any, List, Set, Dict, DefaultDict
from collections import defaultdict
import re

try:
	from common import LoggableSubComponent, cartesiantopolar, loggedmethod, longestcommonprefix
except ImportError:
	from .common import LoggableSubComponent, cartesiantopolar, loggedmethod, longestcommonprefix

try:
	from common import parseValue, formatValue, ValueRange, ValueSequence, ValueRangeSequence
except ImportError:
	from .common import parseValue, formatValue, ValueRange, ValueSequence, ValueRangeSequence


class _ShapePredicate:
	def test(self, shape: ShapeInfo, index: int): raise NotImplementedError()

	def filter(self, shapes: List[ShapeInfo], index: int):
		return [s for s in shapes if self.test(s, index)]

	def describeAtIndex(self, index) -> str:
		raise NotImplementedError()

	def __len__(self):
		return 1

# def _parseRotateAsMatrix(val):
# 	val = parseValue(val)
# 	xform = tdu.Matrix()
# 	if val:
# 		xform.rotate(0, 0, val, pivot=(0, 0, 0))
# 	return xform

class _PositionalPredicate(_ShapePredicate, ABC):
	def __init__(self, groupspec: PositionalGroupGenSpec):
		self.prerotates = ValueSequence.FromSpec(
			groupspec.prerotate,
			parse=float,
			cyclic=True,
			backup=0)

	def test(self, shape: ShapeInfo, index: int):
		pos = tdu.Position(shape.center)
		prerotate = self.prerotates[index]
		if prerotate is not None:
			xform = tdu.Matrix()
			xform.rotate(0, 0, prerotate, pivot=(0, 0, 0))
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

	def describeAtIndex(self, index):
		desc = '(x: {} y: {}'.format(self.xranges[index], self.yranges[index])
		if self.prerotates:
			desc += ' rotate: {}'.format(self.prerotates[index])
		return desc + ')'

	def __len__(self):
		return max(len(self.xranges), len(self.yranges), len(self.prerotates))

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

	def describeAtIndex(self, index):
		desc = '(angle: {} dist: {}'.format(
			self.angleranges.describeAtIndex(index),
			self.distanceranges.describeAtIndex(index))
		if self.prerotates:
			desc += ' rotate: {}'.format(self.prerotates[index])
		return desc + ')'

	def __len__(self):
		return max(len(self.angleranges), len(self.distanceranges), len(self.prerotates))

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
	def __init__(self, shapes: List[ShapeInfo]):
		self.shapes = shapes
		self.groups = []  # type: List[GroupInfo]
		self.groupsbyname = {}  # type: Dict[str, GroupInfo]

	def addGroup(self, group: GroupInfo):
		self.groups.append(group)
		if group.groupname not in self.groupsbyname:
			self.groupsbyname[group.groupname] = group

	def addGroups(self, groups: List[GroupInfo]):
		for group in groups:
			self.addGroup(group)

	def getGroup(self, groupname: str):
		return self.groupsbyname.get(groupname)

	def getGroupsWithShape(self, shapeindex: int):
		return [
			group
			for group in self.groups
			if shapeindex in group.shapeindices
		]

	def getShape(self, shapeindex: int):
		if shapeindex < 0 or shapeindex >= len(self.shapes):
			return None
		return self.shapes[shapeindex]

	def __repr__(self):
		return 'GroupGenContext({} groups, {} shapes)'.format(len(self.groups), len(self.shapes))

class GroupGenerators(LoggableSubComponent):
	def __init__(
			self, hostobj,
			shapes: List[ShapeInfo],
			existinggroups: List[GroupInfo],
			patternsettings: PatternSettings):
		super().__init__(hostobj=hostobj, logprefix='GroupGens')
		self.context = GroupGenContext(shapes)
		self.context.addGroups(existinggroups or [])
		self.patternsettings = patternsettings

	@loggedmethod
	def extractInferredGroups(self, roundingdigits=2):
		extractor = _InferredGroupExtractor(roundingdigits=roundingdigits)
		inferredgroups = extractor.load(self.context.shapes)
		self._LogEvent('Found {} inferred groups'.format(len(inferredgroups)))
		self.context.addGroups(inferredgroups)

	@loggedmethod
	def runGenerators(self):
		generators = GroupGenerator.FromSpecs(hostobj=self, groupspecs=self.patternsettings.groupgens)
		self._LogEvent('Starting with {} groups'.format(len(self.context.groups)))
		self._LogEvent('Loaded {} group generators'.format(len(generators)))
		for generator in generators:
			self._LogEvent('   {}'.format(generator))
			generator.generateGroups(self.context)
		self._LogEvent('Ended with {} groups'.format(len(self.context.groups)))

	def getGroups(self):
		return [
			group
			for group in self.context.groups
			if not group.temporary
		]

class GroupGenerator(LoggableSubComponent, ABC):
	def __init__(self, hostobj, groupspec: GroupGenSpec, logprefix: str=None):
		super().__init__(hostobj=hostobj, logprefix=logprefix or 'GroupGen')
		# self.basedongroups = ValueSequence.FromSpec(groupspec.basedon, cyclic=True)
		self.basename = groupspec.groupname
		if not groupspec.suffixes:
			self.suffixes = None
		else:
			self.suffixes = ValueSequence.FromSpec(groupspec.suffixes, cyclic=False, backup=lambda i: i)
		self.sequencer = None  # type: _ShapeSequencer
		self.temporary = groupspec.temporary

	def _getName(self, index: int, issolo=False):
		name = self.basename
		if self.suffixes is None:
			if index == 0 and issolo:
				return name
			else:
				suffix = 0
		else:
			suffix = self.suffixes[index]
		if self.basename:
			return self.basename + str(suffix)
		return str(suffix)

	def _createGroup(
			self,
			groupname: str,
			context: GroupGenContext,
			shapeindices: List[int]=None,
			autosequence=False):
		if autosequence and shapeindices and self.sequencer:
			steps = self.sequencer.sequenceShapes(shapeindices, context)
		else:
			steps = None
		group = GroupInfo(
			groupname,
			shapeindices=shapeindices,
			sequencesteps=steps,
			temporary=self.temporary)
		return group

	def generateGroups(self, context: GroupGenContext):
		raise NotImplementedError()

	@classmethod
	def FromSpec(cls, hostobj, groupspec: GroupGenSpec):
		if isinstance(groupspec, BoxBoundGroupGenSpec):
			return _BoxBoundGroupGenerator(hostobj, groupspec)
		elif isinstance(groupspec, PolarBoundGroupGenSpec):
			return _PolarBoundGroupGenerator(hostobj, groupspec)
		elif isinstance(groupspec, CombinationGroupGenSpec):
			return _CombinationGroupGenerator(hostobj, groupspec)
		elif isinstance(groupspec, PathGroupGenSpec):
			return _PathGroupGenerator(hostobj, groupspec)
		else:
			raise Exception('Unsupported group gen spec: {} (type: {})'.format(
				groupspec, type(groupspec)))

	@classmethod
	def FromSpecs(cls, hostobj, groupspecs: List[GroupGenSpec]):
		return [cls.FromSpec(hostobj, groupspec) for groupspec in groupspecs]

class _PathGroupGenerator(GroupGenerator):
	def __init__(
			self,
			hostobj,
			groupspec: PathGroupGenSpec):
		super().__init__(hostobj=hostobj, groupspec=groupspec, logprefix='PathGroupGen')
		self.pathpatterns = ValueSequence.FromSpec(groupspec.paths, cyclic=False)
		self.sequencer = _ShapeSequencer.FromSpec(groupspec, hostobj=self)

	@loggedmethod
	def generateGroups(self, context: GroupGenContext):
		groups = []
		n = len(self.pathpatterns)
		self._LogEvent('Paths (len: {})'.format(n))
		for i in range(n):
			pathpattern = self.pathpatterns[i]
			self._LogEvent(' [{}] pattern: {!r}'.format(i, pathpattern))
			shapeindices = [
				shape.shapeindex
				for shape in context.shapes
				if re.match(pathpattern, shape.shapepath)
			]
			self._LogEvent('  found {} shapes'.format(len(shapeindices)))
			if not shapeindices:
				continue
			group = self._createGroup(
				self._getName(i),
				shapeindices=shapeindices,
				context=context,
				autosequence=True,
			)
			self._LogEvent('  produced group: {}'.format(group))
			groups.append(group)
		if len(groups) == 1 and self.suffixes is None:
			groups[0].groupname = self._getName(0, issolo=True)
		context.addGroups(groups)

	def __repr__(self):
		return '{}(basename: {!r}, suffixes: {!r}, paths: {!r})'.format(
			type(self).__name__, self.basename, self.suffixes, self.pathpatterns)

class _PredicateGroupGenerator(GroupGenerator):
	def __init__(
			self,
			hostobj,
			groupspec: GroupGenSpec,
			predicate: _ShapePredicate,
			logprefix: str=None):
		super().__init__(
			hostobj=hostobj,
			logprefix=logprefix,
			groupspec=groupspec)
		self.predicate = predicate
		self.sequencer = _ShapeSequencer.FromSpec(groupspec, hostobj=self)

	@loggedmethod
	def generateGroups(self, context: GroupGenContext):
		groups = []
		n = len(self.predicate)
		self._LogEvent('Predicate: {} (len: {})'.format(self.predicate, n))
		for i in range(n):
			self._LogEvent(' [{}] predicate: {}'.format(i, self.predicate.describeAtIndex(i)))
			groupshapes = []
			for shape in context.shapes:
				if self.predicate.test(shape, i):
					groupshapes.append(shape)
			self._LogEvent('  found {} shapes'.format(len(groupshapes)))
			if not groupshapes:
				continue
			groupshapeindices = [s.shapeindex for s in groupshapes]
			group = self._createGroup(
				groupname=self._getName(i),
				shapeindices=groupshapeindices,
				context=context,
				autosequence=True)
			self._LogEvent('  produced group: {}'.format(group))
			groups.append(group)
		if len(groups) == 1 and self.suffixes is None:
			groups[0].groupname = self._getName(0, issolo=True)
		context.addGroups(groups)

	def __repr__(self):
		return '{}(basename: {!r}, suffixes: {!r}, predicate: {!r})'.format(
			type(self).__name__, self.basename, self.suffixes, self.predicate)

class _BoxBoundGroupGenerator(_PredicateGroupGenerator):
	def __init__(self, hostobj, groupspec: BoxBoundGroupGenSpec):
		super().__init__(
			hostobj=hostobj,
			logprefix='BoxBoundGroupGen',
			groupspec=groupspec,
			predicate=_CartesianPredicate(groupspec),
		)

class _PolarBoundGroupGenerator(_PredicateGroupGenerator):
	def __init__(self, hostobj, groupspec: PolarBoundGroupGenSpec):
		super().__init__(
			hostobj=hostobj,
			logprefix='PolarBoundGroupGen',
			groupspec=groupspec,
			predicate=_PolarPredicate(groupspec),
		)

class _CombinationGroupGenerator(GroupGenerator):
	def __init__(self, hostobj, groupspec: CombinationGroupGenSpec):
		super().__init__(
			hostobj=hostobj,
			logprefix='ComboGroupGen',
			groupspec=groupspec)
		self.groups1 = ValueSequence.FromSpec(groupspec.groups, cyclic=True)
		if groupspec.withgroups is None:
			self.groups2 = self.groups1
		else:
			self.groups2 = ValueSequence.FromSpec(groupspec.withgroups, cyclic=True)
		self.boolop = BoolOpNames.aliases.get(groupspec.boolop) or BoolOpNames.AND
		self.permute = groupspec.permute

	def __repr__(self):
		return '{}(basename: {!r}, suffixes: {!r}, groups1: {!r}, groups2: {!r}, boolop: {!r}, permute: {!r})'.format(
			type(self).__name__, self.basename, self.suffixes,
			self.groups1, self.groups2, self.boolop, self.permute)

	@loggedmethod
	def generateGroups(self, context: GroupGenContext):
		if self.permute:
			groups = self._generatePermutations(context)
		else:
			groups = self._generateBooleanGroups(context)
		if len(groups) == 1 and self.suffixes:
			groups[0].groupname = self._getName(0, issolo=True)
		context.addGroups(groups)

	@loggedmethod
	def _generatePermutations(self, context: GroupGenContext) -> List[GroupInfo]:
		groups = []
		index = 0
		for groupname1 in self.groups1:
			for groupname2 in self.groups2:
				mergedgroup = self._combineGroups(
					groupname1, groupname2,
					index=index, context=context)
				if mergedgroup is not None:
					groups.append(mergedgroup)
				index += 1
		return groups

	@loggedmethod
	def _generateBooleanGroups(self, context: GroupGenContext) -> List[GroupInfo]:
		groups = []
		index = 0
		for groupname1, groupname2 in self.groups1.permuteWith(self.groups2):
			mergedgroup = self._combineGroups(
				groupname1, groupname2,
				index=index, context=context)
			if mergedgroup is not None:
				groups.append(mergedgroup)
			index += 1
		return groups

	def _combineGroups(
			self,
			groupname1: str, groupname2: str,
			index: int,
			context: GroupGenContext):
		group1 = context.getGroup(groupname1)
		group2 = context.getGroup(groupname2)
		if group1 is None:
			self._LogEvent('Unable to find group: {!r}'.format(groupname1))
			return None
		if group2 is None:
			self._LogEvent('Unable to find group: {!r}'.format(groupname2))
			return None
		combiner = _GroupCombiner(hostobj=self)
		combiner.addGroup(group1)
		combiner.addGroup(group2)
		if self.suffixes:
			groupname = self._getName(index, False)
		elif self.basename:
			groupname = self.basename + '_' + groupname1 + '_' + groupname2
		else:
			groupname = groupname1 + '_' + groupname2
		resultgroup = self._createGroup(groupname, context=context, autosequence=False)
		combiner.buildInto(resultgroup, boolop=self.boolop)
		return resultgroup

class _GroupCombiner(LoggableSubComponent):
	def __init__(self, hostobj):
		super().__init__(hostobj, logprefix='GroupCombiner')
		self.sequencegroup = None  # type: GroupInfo
		self.othergroups = []  # type: List[GroupInfo]

	def addGroup(self, group: GroupInfo):
		if group.issequenced:
			if self.sequencegroup:
				self._LogEvent('Ignoring sequencing for group {}'.format(group.groupname))
				self.othergroups.append(group)
			else:
				self.sequencegroup = group
		else:
			self.othergroups.append(group)

	def buildInto(self, resultgroup: GroupInfo, boolop: str):
		boolop = boolop or BoolOpNames.OR
		allshapeindices = self._combineIndexSets(
			[group.shapeindices for group in self.othergroups],
			boolop=boolop
		)
		if not self.sequencegroup:
			resultgroup.sequencesteps = [
				SequenceStep(
					sequenceindex=0,
					isdefault=True,
					shapeindices=list(sorted(allshapeindices)))
			]
			resultgroup.shapeindices = list(sorted(allshapeindices))
		else:
			resultsteps = []  # type: List[SequenceStep]
			finalallstepindices = []
			for basestep in self.sequencegroup.sequencesteps:
				stepindices = self._combineIndexSets(
					[basestep.shapeindices, allshapeindices],
					boolop=boolop
				)
				finalallstepindices += list(stepindices)
				resultsteps.append(SequenceStep(
					sequenceindex=basestep.sequenceindex,
					shapeindices=list(sorted(stepindices))))
			resultgroup.sequencesteps = resultsteps
			resultgroup.shapeindices = list(sorted(set(finalallstepindices)))

	@staticmethod
	def _combineIndexSets(indexsets: List[Set[int]], boolop: str):
		if not indexsets:
			return set()
		combinedindices = set(indexsets[0])
		if boolop == BoolOpNames.AND:
			combinedindices = combinedindices.intersection(*indexsets[1:])
		elif boolop == BoolOpNames.OR:
			combinedindices = combinedindices.union(*combinedindices[1:])
		else:
			return set()
		return combinedindices

class _ShapeSequencer(ABC):
	def sequenceShapes(
			self,
			shapeindices: List[int],
			context: GroupGenContext) -> List[SequenceStep]:
		raise NotImplementedError()

	@staticmethod
	def _createDefaultStep(shapeindices: List[int]):
		return SequenceStep(
			isdefault=True,
			shapeindices=shapeindices
		)

	@classmethod
	def FromSpec(cls, groupspec: GroupGenSpec, hostobj):
		if not groupspec.sequenceby:
			return _NoOpShapeSequencer()
		return _AttributeShapeSequencer(hostobj=hostobj, seqbyspec=groupspec.sequenceby)

class _NoOpShapeSequencer(_ShapeSequencer):
	def sequenceShapes(
			self,
			shapeindices: List[int],
			context: GroupGenContext):
		return [self._createDefaultStep(shapeindices)]

class _AttributeShapeSequencer(LoggableSubComponent, _ShapeSequencer):
	def __init__(
			self, hostobj,
			seqbyspec: SequenceBySpec):
		part = SequenceByTypes.aliases.get(seqbyspec.attr)
		LoggableSubComponent.__init__(
			self, hostobj=hostobj, logprefix='AttrShapeSeq[{}]'.format(part))
		if part in SequenceByTypes.rgb:
			index = SequenceByTypes.rgb.index(part)
			self.accessor = lambda s: s.color[index] if s.color else None
		elif part in SequenceByTypes.hsv:
			index = SequenceByTypes.hsv.index(part)
			self.accessor = lambda s: s.hsvcolor[index] if s.color else None
		elif part == SequenceByTypes.distance:
			self.accessor = lambda s: cartesiantopolar(s.center[0], s.center[1])[0]
		elif part in SequenceByTypes.xy:
			index = SequenceByTypes.xy.index(part)
			self.accessor = lambda s: s.center[index]
		else:
			raise Exception('Unsupported attribute: {!r}'.format(seqbyspec.attr))
		self.rounddigits = seqbyspec.rounddigits
		self.reverse = seqbyspec.reverse
		self.shapesbykey = defaultdict(list)  # type: DefaultDict[Any, List[ShapeInfo]]
		self.unkeyedshapes = []  # type: List[ShapeInfo]

	def _getKey(self, shape: ShapeInfo):
		val = self.accessor(shape)
		if val is None:
			return None
		if self.rounddigits is not None:
			return round(val, self.rounddigits)
		return val

	def _registerShape(self, shape: ShapeInfo):
		key = self._getKey(shape)
		if key is None:
			self.unkeyedshapes.append(shape)
		else:
			self.shapesbykey[key].append(shape)

	def sequenceShapes(
			self,
			shapeindices: List[int],
			context: GroupGenContext):
		self.shapesbykey.clear()
		self.unkeyedshapes.clear()
		if not shapeindices:
			return []
		for shapeindex in shapeindices:
			shape = context.getShape(shapeindex)
			if shape:
				self._registerShape(shape)
		if self.unkeyedshapes:
			self._LogEvent('Group has {} shapes without the required key, putting all shapes in a single default step'.format(
				len(self.unkeyedshapes)))
			return [self._createDefaultStep(shapeindices)]
		steps = []
		stepkeys = list(sorted(self.shapesbykey.keys()))
		if self.reverse:
			stepkeys.reverse()
		for stepindex, stepkey in enumerate(stepkeys):
			steps.append(SequenceStep(
				sequenceindex=stepindex,
				shapeindices=[s.shapeindex for s in self.shapesbykey[stepkey]],
				inferredfromvalue=stepkey,
				isdefault=len(stepkeys) == 1,
			))
		return steps

class _InferredGroupExtractor:
	"""
	Extracts groups from ShapeInfos, based on primitive colors.
	Each unique pair of hue and saturation defines a group of all the matching shapes.
	Within each group, value (as in HSV value) defines the sequence ordering.
	"""
	def __init__(self, roundingdigits=None):
		# list of shapes keyed by (hue, saturation)
		self.shapesbyhuesat = defaultdict(list)  # type: DefaultDict[Tuple, List[ShapeInfo]]
		self.groups = []  # type: List[GroupInfo]
		self.roundingdigits = roundingdigits  # type: int

	def load(self, shapes: List[ShapeInfo]):
		for shape in shapes:
			self._loadShape(shape)
		for huesat, shapes in self.shapesbyhuesat.items():
			self._addGroup(huesat, shapes)
		return self.groups

	def _loadShape(self, shape: ShapeInfo):
		hsvcolor = shape.hsvcolor
		if not hsvcolor:
			return
		key = self._prepareKey(hsvcolor[0], hsvcolor[1])
		self.shapesbyhuesat[key].append(shape)

	def _prepareKey(self, *vals):
		if self.roundingdigits is None:
			return tuple(vals)
		return tuple(round(v, self.roundingdigits) for v in vals)

	def _addGroup(self, huesat, shapes: List[ShapeInfo]):
		shapesbyvalue = defaultdict(list)  # type: DefaultDict[float, List[ShapeInfo]]
		shapeindices = [shape.shapeindex for shape in shapes]
		pathparts = longestcommonprefix([shape.parentpath.split('/') for shape in shapes])
		name = None
		if pathparts:
			cleanedpathparts = [p for p in pathparts if p and not p.startswith('_')]
			if cleanedpathparts:
				name = cleanedpathparts[-1]
		if name:
			if '[' in name and name.endswith(']'):
				name = name.split('[')[1]
				name = name[:-1]
				if name.startswith('id='):
					name = name[3:]
		else:
			groupindex = len(self.groups)
			name = '_{}'.format(groupindex)
		group = GroupInfo(
			groupname=name,
			grouppath='/'.join(pathparts + [name]),
			inferencetype='HS:V',
			inferredfromvalue=huesat,
			shapeindices=list(shapeindices),
		)
		for shape in shapes:
			shapesbyvalue[shape.hsvcolor[2]].append(shape)
		if len(shapesbyvalue) == 1:
			group.sequencesteps.append(SequenceStep(
				sequenceindex=0,
				inferredfromvalue=list(shapesbyvalue.keys())[0],
				shapeindices=list(shapeindices),
			))
		else:
			for i, key in enumerate(sorted(shapesbyvalue.keys())):
				group.sequencesteps.append(
					SequenceStep(
						sequenceindex=i,
						inferredfromvalue=key,
						shapeindices=[shape.shapeindex for shape in shapesbyvalue[key]]
					)
				)
		self.groups.append(group)
