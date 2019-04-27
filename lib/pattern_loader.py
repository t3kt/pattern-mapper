print('pattern_loader.py loading...')

from collections import defaultdict
import json
import xml.etree.ElementTree as ET
from typing import DefaultDict, Dict, List, Set, Tuple

if False:
	from ._stubs import *

# adds the 'packages/' dir to the import path
import td_python_package_init
td_python_package_init.init()

import svg.path as svgpath

try:
	from common import ExtensionBase, LoggableSubComponent
except ImportError:
	from .common import ExtensionBase, LoggableSubComponent

try:
	from common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod, cartesiantopolar
except ImportError:
	from .common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod, cartesiantopolar

try:
	from common import parseValue, parseValueList, formatValue, formatValueList, ValueRange
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList, ValueRange

from pattern_model import BoolOpNames, GroupInfo, GroupSpec, SequenceStep, ShapeInfo, PatternSettings
from pattern_groups import GroupGenerators

remap = tdu.remap

class PatternLoader(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.SvgWidth = tdu.Dependency(1)
		self.SvgHeight = tdu.Dependency(1)
		self.shapes = []  # type: List[ShapeInfo]
		self.groups = []  # type: List[GroupInfo]

	def op(self, path):
		return self.ownerComp.op(path)

	@property
	def _rawShapes(self):
		return self.op('raw_shapes')

	@property
	def TEMP_jsonObj(self):
		return {
			'groups': GroupInfo.ToJsonDicts(self.groups)
		}

	@property
	def PatternJsonFileName(self):
		svgname = self.ownerComp.par.Svgfile.eval()
		if not svgname:
			return ''
		if svgname.endswith('.svg'):
			return svgname.replace('.svg', '.json')
		return ''

	@simpleloggedmethod
	def BuildGeometryFromSvg(self, sop, svgxml):
		self._BuildGeometryFromSvg(sop, svgxml)
		self._BuildGroups()

	@loggedmethod
	def _BuildGeometryFromSvg(self, sop, svgxml):
		parser = _SvgParser(self, sop)
		parser.parse(
			svgxml,
			recenter=self.ownerComp.par.Recenter,
			rescale=self.ownerComp.par.Rescale)
		self.SvgWidth.val = parser.svgwidth
		self.SvgHeight.val = parser.svgheight
		self.shapes = parser.shapes
		self.groups = []
		for o in self.ownerComp.ops('build_shape_attr_table'):
			o.cook(force=True)

	@loggedmethod
	def ConvertShapePathsToPanels(self, sop, insop):
		sop.copy(insop)
		while len(sop.prims):
			sop.prims[0].destroy()
		while len(sop.points):
			sop.points[0].destroy()
		for srcpoly in insop.prims:
			poly = sop.appendPoly(len(srcpoly) - 1, addPoints=True, closed=True)
			# for some reason using getattr() on points/prims/vertices/etc causes TD to crash
			# so they need to be hard-coded
			_copyAttrVals(toattr=poly.Cd, fromattr=srcpoly.Cd)
			poly.shapeIndex[0] = srcpoly.shapeIndex[0]
			for vertex in poly:
				srcvertex = srcpoly[vertex.index]
				vertex.point.x = srcvertex.point.x
				vertex.point.y = srcvertex.point.y
				vertex.point.z = srcvertex.point.z
				_copyAttrVals(toattr=vertex.absRelDist, fromattr=srcvertex.absRelDist)
				_copyAttrVals(toattr=vertex.uv, fromattr=srcvertex.uv)
				_copyAttrVals(toattr=vertex.centerPos, fromattr=srcvertex.centerPos)

	@loggedmethod
	def BuildGroupTable(self, dat):
		if not self.groups:
			self._BuildGroups()
		dat.clear()
		dat.appendRow([
			'groupname',
			'grouppath',
			'inferencetype',
			'inferredfromvalue',
			'sequencelength',
			'shapecount',
			'shapes',
		])
		for groupinfo in self.groups:
			dat.appendRow([
				groupinfo.groupname or '',
				groupinfo.grouppath or '',
				groupinfo.inferencetype or '',
				groupinfo.inferredfromvalue if groupinfo.inferredfromvalue is not None else '',
				len(groupinfo.sequencesteps),
				len(groupinfo.shapeindices),
				' '.join(map(str, groupinfo.shapeindices)),
			])

	@loggedmethod
	def BuildSequenceStepTable(self, dat):
		dat.clear()
		dat.appendRow([
			'groupname',
			'sequenceindex',
			'isdefault',
			'inferredfromvalue',
			'shapes',
		])
		if not self.groups:
			return
		for groupinfo in self.groups:
			for step in groupinfo.sequencesteps:
				if not step.shapeindices:
					continue
				dat.appendRow([
					groupinfo.groupname,
					step.sequenceindex,
					int(step.isdefault or 0),
					step.inferredfromvalue if step.inferredfromvalue is not None else '',
					' '.join(map(str, step.shapeindices)),
				])

	@loggedmethod
	def BuildShapeAttrTable(self, dat):
		dat.clear()
		dat.appendRow([
			'shapeindex', 'shapename', 'shapepath', 'parentpath',
			'colorr', 'colorg', 'colorb',
			'colorh', 'colors', 'colorv',
			'centerx', 'centery', 'centerz',
			'centerangle', 'centerdist',
			'shapelength',
		])
		for shape in self.shapes:
			r = dat.numRows
			dat.appendRow([])
			dat[r, 'shapeindex'] = shape.shapeindex
			dat[r, 'shapename'] = shape.shapename or ''
			dat[r, 'shapepath'] = shape.shapepath or ''
			dat[r, 'parentpath'] = shape.parentpath or ''
			color = shape.color or [0, 0, 0]
			dat[r, 'colorr'] = formatValue(color[0])
			dat[r, 'colorg'] = formatValue(color[1])
			dat[r, 'colorb'] = formatValue(color[2])
			hsvcolor = shape.hsvcolor or [0, 0, 0]
			dat[r, 'colorh'] = formatValue(hsvcolor[0])
			dat[r, 'colors'] = formatValue(hsvcolor[1])
			dat[r, 'colorv'] = formatValue(hsvcolor[2])
			if shape.center:
				dat[r, 'centerx'] = formatValue(shape.center[0])
				dat[r, 'centery'] = formatValue(shape.center[1])
				dat[r, 'centerz'] = formatValue(shape.center[2])
				distance, angle = cartesiantopolar(shape.center[0], shape.center[1])
				dat[r, 'centerangle'] = formatValue(angle)
				dat[r, 'centerdist'] = formatValue(distance)
			dat[r, 'shapelength'] = formatValue(shape.shapelength, nonevalue='')

	# Build a chop with a channel for each group and a sample for each shape.
	# For each sample and group, the value is either the sequenceIndex, or -1 if the shape
	# is not in that group.
	@loggedmethod
	def BuildShapeGroupSequenceIndices(self, chop):
		chop.clear()
		numshapes = len(self.shapes)
		chop.numSamples = numshapes
		if not self.groups:
			self._BuildGroups()
		for group in self.groups:
			chan = chop.appendChan('seq_' + group.groupname)
			shapesteps = [-1] * numshapes
			for step in group.sequencesteps:
				for shapeindex in step.shapeindices:
					if shapesteps[shapeindex] == -1:
						shapesteps[shapeindex] = step.sequenceindex
			for shapeindex in range(numshapes):
				chan[shapeindex] = shapesteps[shapeindex]

	@loggedmethod
	def _BuildGroups(self):
		builder = _GroupsBuilder(self, self.shapes)
		builder.loadImplicitGroups()

		jsondat = self.op('load_json_file')
		jsondat.clear()
		jsondat.par.loadonstartpulse.pulse()
		obj = json.loads(jsondat.text) if jsondat.text else {}
		patternsettings = PatternSettings.FromJsonDict(obj)

		self.groups = builder.grouplist

		generators = GroupGenerators(
			hostobj=self,
			shapes=self.shapes,
			existinggroups=self.groups,
			patternsettings=patternsettings)
		self.groups = generators.runGenerators()

		for o in self.ownerComp.ops('build_group_table', 'build_sequence_step_table'):
			o.cook(force=True)

	@staticmethod
	def SetUVLayerToLocalPos(sop, uvlayer: int):
		for prim in sop.prims:
			for vertex in prim:
				vertex.uv[(uvlayer * 3) + 0] = remap(vertex.point.x, prim.min.x, prim.max.x, 0, 1)
				vertex.uv[(uvlayer * 3) + 1] = remap(vertex.point.y, prim.min.y, prim.max.y, 0, 1)

	@staticmethod
	def FixFaceFlipping(sop):
		fixFaceFlipping(sop)

	def BuildPathLookupTable(self, chop, tablelength):
		chop.clear()
		shapes = self._rawShapes
		shapecount = shapes.numPrims
		chop.numSamples = tablelength
		for shapeindex in range(shapecount):
			xchan = chop.appendChan('shape{}:tx'.format(shapeindex))
			ychan = chop.appendChan('shape{}:ty'.format(shapeindex))
			zchan = chop.appendChan('shape{}:tz'.format(shapeindex))
			prim = shapes.prims[shapeindex]
			for i in range(tablelength):
				pos = prim.eval(i / (tablelength - 1), 0)
				xchan[i] = pos.x
				ychan[i] = pos.y
				zchan[i] = pos.z


class _SvgParser(LoggableSubComponent):
	def __init__(self, hostobj, sop):
		super().__init__(hostobj=hostobj, logprefix='SvgParser')
		self.svgwidth = 0
		self.svgheight = 0
		self.sop = sop
		self.scale = 1
		self.offset = tdu.Vector(0, 0, 0)
		self.shapes = []  # type: List[ShapeInfo]

	def parse(self, svgxml, recenter=True, rescale=True):
		sop = self.sop
		sop.clear()
		if not svgxml:
			return
		sop.primAttribs.create('Cd')
		# distance around path (absolute), distance around path (relative to shape length)
		sop.vertexAttribs.create('absRelDist', (0.0, 0.0))
		root = ET.fromstring(svgxml)
		self.svgwidth = float(root.get('width', 1))
		self.svgheight = float(root.get('height', 1))
		self.scale = 1 / max(self.svgwidth, self.svgheight)
		self.offset = tdu.Vector(-self.svgwidth / 2, -self.svgheight / 2, 0)
		self._handleElem(root, 0, namestack=[])
		self._postProcessCoords(recenter=recenter, rescale=rescale)

	def _postProcessCoords(self, recenter=True, rescale=True):
		if recenter:
			offset = -self.sop.center
			for point in self.sop.points:
				point.x += offset.x
				point.y += offset.y
				point.z += offset.z
		if rescale:
			scale = 1 / max(self.sop.size.x, self.sop.size.y, self.sop.size.z)
			for point in self.sop.points:
				point.x *= scale
				point.y *= scale
				point.z *= scale
		for shape in self.shapes:
			poly = self.sop.prims[shape.shapeindex]
			shape.center = poly.center.x, poly.center.y, poly.center.z

	@staticmethod
	def _elemName(elem: ET.Element, indexinparent: int):
		tagname = _localName(elem.tag)
		elemid = elem.get('id')
		if tagname == 'svg':
			suffix = ''
		elif elemid:
			suffix = '[id={}]'.format(elemid)
		else:
			suffix = '[{}]'.format(indexinparent)
		return tagname + suffix

	def _handleElem(self, elem: ET.Element, indexinparent: int, namestack: List[str]):
		elemname = self._elemName(elem, indexinparent)
		elemid = elem.get('id', '')
		if elemid == 'Background' or elemid.startswith('-'):
			self._LogEvent('Skipping element: {}'.format(ET.tostring(elem)))
			return
		if elem.get('display') == 'none':
			self._LogEvent('Skipping element: {}'.format(ET.tostring(elem)))
			return
		tagname = _localName(elem.tag)
		if tagname == 'path':
			self._handlePathElem(elem, elemname=elemname, namestack=namestack)
		else:
			childnamestack = namestack + [elemname]
			for childindex, childelem in enumerate(list(elem)):
				self._handleElem(childelem, childindex, namestack=childnamestack)

	def _handlePathElem(self, pathelem, elemname: str, namestack: List[str]):
		rawpath = pathelem.get('d')
		path = svgpath.parse_path(rawpath)
		if len(path) < 2:
			raise Exception('Unsupported path (too short) {}'.format(rawpath))
		firstsegment = path[0]
		if not isinstance(firstsegment, svgpath.Move):
			raise Exception('Unsupported path (must start with Move) {}'.format(rawpath))
		pathpoints = [_pathPoint(firstsegment.start)]
		for segment in path[1:]:
			if isinstance(segment, (svgpath.CubicBezier, svgpath.QuadraticBezier)):
				self._LogEvent('WARNING: treating bezier as line {}'.format(rawpath))
			elif not isinstance(segment, svgpath.Line):
				raise Exception('Unsupported path (can only contain Line after first segment) {} {}'.format(
					type(segment), rawpath))
			pathpt = _pathPoint(segment.end)
			pathpoints.append(pathpt)
		# if pathpoints[-1] == pathpoints[0]:
		# 	pathpoints.pop()
		poly = self.sop.appendPoly(len(pathpoints), addPoints=True, closed=False)
		totaldist = path.length()
		distances = _segmentDistances(path, self.scale)
		totaldist *= self.scale
		shape = ShapeInfo(
			shapeindex=poly.index,
			shapename=pathelem.get('id', None),
			shapepath='/'.join(namestack + [elemname]),
			parentpath='/'.join(namestack),
			color=_getPathElementColor(pathelem),
			shapelength=totaldist,
		)
		if shape.color:
			poly.Cd[0] = shape.color[0] / 255.0
			poly.Cd[1] = shape.color[1] / 255.0
			poly.Cd[2] = shape.color[2] / 255.0
		else:
			poly.Cd[0] = poly.Cd[1] = poly.Cd[2] = 1
		poly.Cd[3] = 1
		for i, pathpt in enumerate(pathpoints):
			vertex = poly[i]
			pos = (pathpt + self.offset) * self.scale
			vertex.point.x = pos.x
			vertex.point.y = pos.y
			vertex.absRelDist[0] = distances[i]
			vertex.absRelDist[1] = distances[i] / totaldist
		self.shapes.append(shape)


def _localName(fullname: str):
	if '}' in fullname:
		return fullname.rsplit('}', maxsplit=1)[1]
	elif ':' in fullname:
		return fullname.rsplit(':', maxsplit=1)[1]
	else:
		return fullname

def _copyAttrVals(toattr, fromattr):
	for i in range(len(fromattr)):
		toattr[i] = fromattr[i]

def fixFaceFlipping(sop):
	for prim in sop.prims:
		if prim.normal.z < 0:
			origpoints = [v.point for v in prim]
			origuvs = [_attrDataToTuple(v.uv) for v in prim]
			n = len(prim)
			for i in range(n):
				prim[i].point = origpoints[-i]
				_setAttrDataFromTuple(prim[i].uv, origuvs[-i])

def _attrDataToTuple(attrdata):
	return tuple(attrdata[i] for i in range(len(attrdata)))

def _setAttrDataFromTuple(attrdata, values):
	for i in range(len(values)):
		attrdata[i] = values[i]

def _getPathElementColor(pathelem):
	if 'stroke' in pathelem.attrib:
		return hextorgb(pathelem.attrib['stroke'])
	elif 'fill' in pathelem.attrib:
		return hextorgb(pathelem.attrib['fill'])
	else:
		return None

def _segmentDistances(path: svgpath.Path, scale):
	distsofar = 0
	distances = [0]
	for segment in path[1:]:
		distsofar += segment.length() * scale
		distances.append(distsofar)
	return distances

def _pathPoint(pathpt: complex):
	return tdu.Position(pathpt.real, pathpt.imag, 0)

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
		pathparts = _longestCommonPrefix([shape.parentpath.split('/') for shape in shapes])
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

def _longestCommonPrefix(strs):
	if not strs:
		return []
	for i, letter_group in enumerate(zip(*strs)):
		# ["flower","flow","flight"]
		# print(i,letter_group,set(letter_group))
		# 0 ('f', 'f', 'f') {'f'}
		if len(set(letter_group)) > 1:
			return strs[0][:i]
	else:
		return min(strs)

class _GroupsBuilder(LoggableSubComponent):
	def __init__(self, hostobj, shapes: List[ShapeInfo]):
		super().__init__(hostobj, logprefix='_GroupsBuilder')
		self.shapes = shapes or []
		self.grouplist = []  # type: List[GroupInfo]
		self.groupsbyname = {}  # type: Dict[str, GroupInfo]

	def hasGroup(self, groupname):
		return groupname in self.groupsbyname

	@loggedmethod
	def loadImplicitGroups(self):
		implicitgroups = _InferredGroupExtractor(roundingdigits=4).load(self.shapes)
		for group in implicitgroups:
			self._addGroup(group)

	@loggedmethod
	def loadGroupSpecs(self, groupspecs: List[GroupSpec]):
		for groupspec in groupspecs:
			groups = self._createGroupsFromSpec(groupspec) or []
			self._LogEvent('spec: {}, groups: {}'.format(groupspec, groups))
			for group in groups:
				self._addGroup(group)

	@loggedmethod
	def _createGroupsFromSpec(self, groupspec: GroupSpec):
		if not groupspec.groupname or groupspec.groupname.startswith('-'):
			return None
		if groupspec.inferencetype or groupspec.inferredfromvalue:
			raise Exception('Inference not yet supported for group specs {!r}'.format(groupspec))
		groupspec.validate()
		group = GroupInfo(
			groupname=groupspec.groupname,
			grouppath=groupspec.grouppath,
			shapeindices=list(groupspec.shapeindices),
			**groupspec.attrs,
		)

		try:
			if groupspec.ismanual:
				self._initManualGroup(group, groupspec)
			elif groupspec.iscombination:
				self._initCombinedGroup(group, groupspec)
			elif groupspec.isbounded:
				self._initBoundedGroup(group, groupspec)
		except Exception as e:
			self._LogEvent('Skipping group due to error: {}'.format(e))
			return None

		return [group]

	@simpleloggedmethod
	def _initManualGroup(self, group: GroupInfo, groupspec: GroupSpec):
		group.shapeindices = list(groupspec.shapeindices)
		for step in groupspec.sequencesteps:
			group.sequencesteps.append(SequenceStep(
				sequenceindex=step.sequenceindex,
				shapeindices=step.shapeindices,
				isdefault=step.isdefault,
				inferredfromvalue=step.inferredfromvalue,
				**step.attrs,
			))
			for shapeindex in step.shapeindices:
				if shapeindex not in group.shapeindices:
					group.shapeindices.append(shapeindex)

	@simpleloggedmethod
	def _initCombinedGroup(self, group: GroupInfo, groupspec: GroupSpec):
		combiner = _GroupCombiner(hostobj=self)
		for basedonname in groupspec.basedon:
			basedongroup = self.groupsbyname.get(basedonname, None)
			if not basedongroup:
				raise Exception('Basis group not found {!r} for {!r}'.format(basedonname, groupspec))
			combiner.addGroup(basedongroup)
		group.inferencetype = groupspec.boolop or BoolOpNames.OR
		group.inferredfromvalue = groupspec.basedon
		combiner.buildInto(resultgroup=group, boolop=groupspec.boolop)

	@simpleloggedmethod
	def _initBoundedGroup(self, group: GroupInfo, groupspec: GroupSpec):
		predicate = _boundsPredicates(groupspec)
		shapeindices = []
		for shape in self.shapes:
			if predicate.test(shape) and shape.shapeindex not in shapeindices:
				shapeindices.append(shape.shapeindex)
		group.shapeindices = shapeindices
		if not group.sequencesteps:
			group.sequencesteps.append(SequenceStep(
				sequenceindex=0,
				shapeindices=shapeindices,
				isdefault=True,
			))
		else:
			step = group.sequencesteps[0]
			step.isdefault = True
			step.shapeindices = list(shapeindices)
		group.inferencetype = 'bounded'
		group.inferredfromvalue = repr(predicate)

	@loggedmethod
	def _addGroup(self, group: GroupInfo):
		self.grouplist.append(group)
		if group.groupname:
			if group.groupname in self.groupsbyname:
				self._LogEvent('ignoring duplicate group name {!r}'.format(group.groupname))
			else:
				self.groupsbyname[group.groupname] = group

class _ShapePredicate:
	def test(self, shape: ShapeInfo): raise NotImplementedError()

class _CartesianPredicate(_ShapePredicate):
	def __init__(self, groupspec: GroupSpec):
		self.xform = tdu.Matrix()
		self.prerotate = groupspec.prerotate
		if groupspec.prerotate:
			self.xform.rotate(0, 0, groupspec.prerotate, pivot=(0, 0, 0))
		self.xtest = ValueRange(groupspec.xbound)
		self.ytest = ValueRange(groupspec.ybound)

	def __repr__(self):
		desc = '(x: {} y: {}'.format(self.xtest, self.ytest)
		if self.prerotate:
			desc += ' rotated: {}'.format(self.prerotate)
		return desc + ')'

	def test(self, shape: ShapeInfo):
		pos = tdu.Position(shape.center)
		pos *= self.xform
		return self.xtest.contains(pos.x) and self.ytest.contains(pos.y)

class _PolarPredicate(_ShapePredicate):
	def __init__(self, groupspec: GroupSpec):
		self.xform = tdu.Matrix()
		self.prerotate = groupspec.prerotate
		if groupspec.prerotate:
			self.xform.rotate(0, 0, groupspec.prerotate, pivot=(0, 0, 0))
		self.angletest = ValueRange(groupspec.anglebound)
		self.disttest = ValueRange(groupspec.distancebound)

	def __repr__(self):
		desc = '(angle: {} dist: {}'.format(self.angletest, self.disttest)
		if self.prerotate:
			desc += ' rotated: {}'.format(self.prerotate)
		return desc + ')'

	def test(self, shape: ShapeInfo):
		pos = tdu.Position(shape.center)
		pos *= self.xform
		dist, angle = cartesiantopolar(pos.x, pos.y)
		return self.disttest.contains(dist) and self.angletest.contains(angle)

class _MultiPredicate(_ShapePredicate):
	def __init__(self, *predicates: _ShapePredicate):
		self.predicates = [p for p in predicates if p is not None]

	def test(self, shape: ShapeInfo):
		if not self.predicates:
			return True
		return any([p.test(shape) for p in self.predicates])

	def __repr__(self):
		return ' '.join([repr(p) for p in self.predicates])

def _boundsPredicates(groupspec: GroupSpec):
	return _MultiPredicate(
		_CartesianPredicate(groupspec) if groupspec.xbound or groupspec.ybound else None,
		_PolarPredicate(groupspec) if groupspec.distancebound or groupspec.anglebound else None,
	)

class _GroupCombiner(LoggableSubComponent):
	def __init__(self, hostobj):
		super().__init__(hostobj, logprefix='_GroupCombiner')
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
