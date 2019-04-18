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

from pattern_model import BoolOpNames, GroupInfo, GroupSpec, SequenceStep, ShapeInfo

remap = tdu.remap

class PatternLoader(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.SvgWidth = tdu.Dependency(1)
		self.SvgHeight = tdu.Dependency(1)
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
		self._BuildGroups(sop)

	@loggedmethod
	def _BuildGeometryFromSvg(self, sop, svgxml):
		self.SvgWidth.val = 0
		self.SvgHeight.val = 0
		sop.clear()
		if not svgxml:
			return
		sop.primAttribs.create('shapeId', '')
		sop.primAttribs.create('parentPath', '')
		sop.primAttribs.create('Cd')
		sop.primAttribs.create('shapeLength', 0.0)
		# distance around path (absolute), distance around path (relative to shape length)
		sop.vertexAttribs.create('absRelDist', (0.0, 0.0))
		root = ET.fromstring(svgxml)
		self.SvgWidth.val = float(root.get('width', 1))
		self.SvgHeight.val = float(root.get('height', 1))
		scale = 1 / max(self.SvgWidth.val, self.SvgHeight.val)
		offset = tdu.Vector(-self.SvgWidth.val / 2, -self.SvgHeight.val / 2, 0)

		def _handleElem(elem : ET.Element, indexinparent, parentpath=''):
			elemid = elem.get('id')
			if elemid and (elemid == 'Background' or elemid.startswith('-')):
				self._LogEvent('Skipping element: {}'.format(ET.tostring(elem)))
				return
			if elem.get('display') == 'none':
				self._LogEvent('Skipping element: {}'.format(ET.tostring(elem)))
				return
			tagname = _localname(elem.tag)
			if tagname == 'path':
				# self._LogEvent('Handling path element: {}'.format(ET.tostring(elem)))
				_handlePathElem(elem, parentpath=parentpath)
			else:
				# self._LogEvent('Handling group element: {}'.format(ET.tostring(elem)))
				elemid = elemid or '_{}'.format(indexinparent)
				if parentpath:
					childparentpath = parentpath + '/' + elemid
				else:
					childparentpath = elemid
				for childindex, childelem in enumerate(list(elem)):
					_handleElem(childelem, childindex, childparentpath)

		def _handlePathElem(pathelem, parentpath):
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
			poly = sop.appendPoly(len(pathpoints), addPoints=True, closed=False)
			totaldist = path.length()
			distances = _segmentDistances(path, scale)
			totaldist *= scale
			poly.shapeLength[0] = totaldist
			poly.shapeId[0] = pathelem.get('id', '')
			poly.parentPath[0] = parentpath
			_applyPathColor(poly, pathelem)
			for i, pathpt in enumerate(pathpoints):
				vertex = poly[i]
				pos = (pathpt + offset) * scale
				vertex.point.x = pos.x
				vertex.point.y = pos.y
				vertex.absRelDist[0] = distances[i]
				vertex.absRelDist[1] = distances[i] / totaldist

		_handleElem(root, 0)

	@loggedmethod
	def ConvertShapePathsToPanels(self, sop, insop):
		sop.copy(insop)
		while len(sop.prims):
			sop.prims[0].destroy()
		while len(sop.points):
			sop.points[0].destroy()
		# primattrs = list(sop.primAttribs)
		# vertattrs = list(sop.vertexAttribs)
		# pointattrs = list(sop.pointAttribs)
		for srcpoly in insop.prims:
			poly = sop.appendPoly(len(srcpoly) - 1, addPoints=True, closed=True)
			# self._copyGeoAttribs(
			# 	fromobj=srcpoly,
			# 	toobj=poly,
			# 	attribs=primattrs)
			# for some reason using getattr() on points/prims/vertices/etc causes TD to crash
			# so they need to be hard-coded
			_copyAttrVals(toattr=poly.shapeId, fromattr=srcpoly.shapeId)
			_copyAttrVals(toattr=poly.parentPath, fromattr=srcpoly.parentPath)
			_copyAttrVals(toattr=poly.Cd, fromattr=srcpoly.Cd)
			_copyAttrVals(toattr=poly.shapeLength, fromattr=srcpoly.shapeLength)
			_copyAttrVals(toattr=poly.polarCenter, fromattr=srcpoly.polarCenter)
			_copyAttrVals(toattr=poly.centerPos_prim, fromattr=srcpoly.centerPos_prim)
			for vertex in poly:
				srcvertex = srcpoly[vertex.index]
				vertex.point.x = srcvertex.point.x
				vertex.point.y = srcvertex.point.y
				vertex.point.z = srcvertex.point.z
				_copyAttrVals(toattr=vertex.absRelDist, fromattr=srcvertex.absRelDist)
				_copyAttrVals(toattr=vertex.uv, fromattr=srcvertex.uv)
				_copyAttrVals(toattr=vertex.centerPos, fromattr=srcvertex.centerPos)
				# _copyAttrVals(toattr=vertex.centerPos)
				# _copyAttrVals(toattr=vertex.)
				# self._copyGeoAttribs(
				# 	fromobj=srcvertex,
				# 	toobj=vertex,
				# 	attribs=vertattrs)
				# self._copyGeoAttribs(
				# 	fromobj=srcvertex.point,
				# 	toobj=vertex.point,
				# 	attribs=pointattrs)

	@loggedmethod
	def _copyGeoAttribs(self, toobj, fromobj, attribs: List['td.Attribute']):
		for attrib in attribs:
			# if attrib.name not in []:
			# 	self._LogEvent('skipping attribute {}'.format(attrib))
			# 	continue
			# else:
			# 	self._LogEvent('copying attribute {}'.format(attrib))
			# self._LogEvent('  from has it: {}'.format(hasattr(fromobj, attrib.name)))
			# todata = getattr(toobj, attrib.name)
			# fromdata = getattr(fromobj, attrib.name, attrib.default)
			# for i in range(attrib.size):
			# 	todata[i] = fromdata[i]
			# _copyAttrVals(toattr=todata, fromattr=fromdata)
			pass

	@loggedmethod
	def BuildGroupTable(self, dat):
		if not self.groups:
			self._BuildGroups(sop=self._rawShapes)
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

	# Build a chop with a channel for each group and a sample for each shape.
	# For each sample and group, the value is either the sequenceIndex, or -1 if the shape
	# is not in that group.
	@loggedmethod
	def BuildShapeGroupSequenceIndices(self, chop):
		chop.clear()
		rawshapes = self._rawShapes
		numshapes = rawshapes.numPrims
		chop.numSamples = numshapes
		if not self.groups:
			self._BuildGroups(sop=rawshapes)
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
	def _BuildGroups(self, sop):
		shapes = _shapeInfosFromPolys(sop.prims)
		builder = _GroupsBuilder(self, shapes)
		builder.loadImplicitGroups()

		jsondat = self.op('load_json_file')
		jsondat.clear()
		jsondat.par.loadonstartpulse.pulse()
		obj = json.loads(jsondat.text) if jsondat.text else {}

		if obj.get('autosides'):
			if not builder.hasGroup('tophalf'):
				builder.loadGroupSpecs([GroupSpec('tophalf', ybound=(0, None))])
			if not builder.hasGroup('bottomhalf'):
				builder.loadGroupSpecs([GroupSpec('bottomhalf', ybound=(None, 0))])
			if not builder.hasGroup('left'):
				builder.loadGroupSpecs([GroupSpec('lefthalf', xbound=(None, 0))])
			if not builder.hasGroup('right'):
				builder.loadGroupSpecs([GroupSpec('righthalf', xbound=(0, None))])

		groupspecs = GroupSpec.FromJsonDicts(obj.get('groups'))
		if groupspecs:
			builder.loadGroupSpecs(groupspecs)
		self.groups = builder.grouplist

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

def _localname(fullname: str):
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

def _applyPathColor(poly, pathelem):
	if 'stroke' in pathelem.attrib:
		rgb = hextorgb(pathelem.attrib['stroke'])
	elif 'fill' in pathelem.attrib:
		rgb = hextorgb(pathelem.attrib['fill'])
	else:
		rgb = (255, 255, 255)
	poly.Cd[0] = rgb[0] / 255.0
	poly.Cd[1] = rgb[1] / 255.0
	poly.Cd[2] = rgb[2] / 255.0
	poly.Cd[3] = 1

def _segmentDistances(path: svgpath.Path, scale):
	distsofar = 0
	distances = [0]
	for segment in path[1:]:
		distsofar += segment.length() * scale
		distances.append(distsofar)
	return distances

def _pathPoint(pathpt: complex):
	return tdu.Position(pathpt.real, pathpt.imag, 0)

def _shapeInfosFromPolys(polys):
	return [
		ShapeInfo(
			shapeindex=poly.index,
			shapename=poly.shapeId[0],
			parentpath=poly.parentPath[0],
			color=(round(255 * poly.Cd[0]), round(255 * poly.Cd[1]), round(255 * poly.Cd[2])),
			center=(poly.center.x, poly.center.y, poly.center.z),
		)
		for poly in polys
	]

class _InferredGroupExtractor:
	"""
	Extracts groups from ShapeInfos, based on primitive colors.
	Each unique pair of hue and saturation defines a group of all the matching shapes.
	Within each group, value (as in HSV value) defines the sequence ordering.
	"""
	def __init__(self):
		# list of shapes keyed by (hue, saturation)
		self.shapesbyhuesat = defaultdict(list)  # type: DefaultDict[Tuple, List[ShapeInfo]]
		self.groups = []  # type: List[GroupInfo]

	def load(self, shapes: List[ShapeInfo]):
		for shape in shapes:
			self._loadshape(shape)
		for huesat, shapes in self.shapesbyhuesat.items():
			self._addgroup(huesat, shapes)
		return self.groups

	def _loadshape(self, shape: ShapeInfo):
		hsvcolor = shape.hsvcolor
		if not hsvcolor:
			return
		self.shapesbyhuesat[(hsvcolor[0], hsvcolor[1])].append(shape)

	def _addgroup(self, huesat, shapes: List[ShapeInfo]):
		shapesbyvalue = defaultdict(list)  # type: DefaultDict[float, List[ShapeInfo]]
		shapeindices = [shape.shapeindex for shape in shapes]
		pathparts = _longestCommonPrefix([shape.parentpath.split('/') for shape in shapes])
		name = None
		if pathparts:
			cleanedpathparts = [p for p in pathparts if p and not p.startswith('_')]
			if cleanedpathparts:
				name = cleanedpathparts[-1]
		if not name:
			groupindex = len(self.groups)
			name = '_{}'.format(groupindex)
		group = GroupInfo(
			groupname=name,
			grouppath='/'.join(pathparts),
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
		return ""
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
		implicitgroups = _InferredGroupExtractor().load(self.shapes)
		for group in implicitgroups:
			self._addGroup(group)

	@loggedmethod
	def loadGroupSpecs(self, groupspecs: List[GroupSpec]):
		for groupspec in groupspecs:
			group = self._createGroupFromSpec(groupspec)
			if group:
				self._addGroup(group)

	@loggedmethod
	def _createGroupFromSpec(self, groupspec: GroupSpec):
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

		return group

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
				print('ignoring duplicate group name {!r}'.format(group.groupname))
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
		self.xmin, self.xmax = groupspec.xbound or (None, None)
		self.ymin, self.ymax = groupspec.ybound or (None, None)

	def __repr__(self):
		desc = '(x: {} '.format([v if v is not None else '*' for v in (self.xmin, self.xmax)])
		desc += 'y: {}'.format([v if v is not None else '*' for v in (self.ymin, self.ymax)])
		if self.prerotate:
			desc += ' rotated: {}'.format(self.prerotate)
		return desc + ')'

	def test(self, shape: ShapeInfo):
		pos = tdu.Position(shape.center)
		pos *= self.xform
		if self.xmin is not None and pos.x < self.xmin:
			return False
		if self.xmax is not None and pos.x > self.xmax:
			return False
		if self.ymin is not None and pos.y < self.ymin:
			return False
		if self.ymax is not None and pos.y > self.ymax:
			return False
		return True

class _PolarPredicate(_ShapePredicate):
	def __init__(self, groupspec: GroupSpec):
		self.xform = tdu.Matrix()
		self.prerotate = groupspec.prerotate
		if groupspec.prerotate:
			self.xform.rotate(0, 0, groupspec.prerotate, pivot=(0, 0, 0))
		self.tmin, self.tmax = groupspec.thetabound or (None, None)
		self.rmin, self.rmax = groupspec.distancebound or (None, None)

	def __repr__(self):
		desc = '(t: {} '.format([v if v is not None else '*' for v in (self.tmin, self.tmax)])
		desc += 'r: {}'.format([v if v is not None else '*' for v in (self.rmin, self.rmax)])
		if self.prerotate:
			desc += ' rotated: {}'.format(self.prerotate)
		return desc + ')'

	def test(self, shape: ShapeInfo):
		pos = tdu.Position(shape.center)
		pos *= self.xform
		dist, theta = cartesiantopolar(pos.x, pos.y)
		if self.rmin is not None and dist < self.rmin:
			return False
		if self.rmax is not None and dist > self.rmax:
			return False
		if self.tmin is not None and theta < self.tmin:
			return False
		if self.tmax is not None and theta > self.tmax:
			return False
		return True

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
		_PolarPredicate(groupspec) if groupspec.distancebound or groupspec.thetabound else None,
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
		self._LogEvent('.. shapeindices: {}'.format(resultgroup.shapeindices))
		self._LogEvent('.. steps: {}'.format(resultgroup.sequencesteps))

	@loggedmethod
	def _combineIndexSets(self, indexsets: List[Set[int]], boolop: str):
		if not indexsets:
			return set()
		combinedindices = set(indexsets[0])
		if boolop == BoolOpNames.AND:
			combinedindices = combinedindices.intersection(*indexsets[1:])
		elif boolop == BoolOpNames.OR:
			combinedindices = combinedindices.union(*combinedindices[1:])
		else:
			return set()
		self._LogEvent('result: {}'.format(combinedindices))
		return combinedindices
