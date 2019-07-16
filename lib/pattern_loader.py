print('pattern_loader.py loading...')

import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Union
import pathlib

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
	from common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod, cartesiantopolar, longestcommonprefix
except ImportError:
	from .common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod, cartesiantopolar, longestcommonprefix

try:
	from common import parseValue, parseValueList, formatValue, formatValueList, ValueRange, averagePoints
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList, ValueRange, averagePoints

from pattern_model import GroupInfo, ShapeInfo, PatternSettings, DepthLayeringSpec, PatternData, PointData
from pattern_groups import GroupGenerators
from pattern_state import ShapeStatesBuilder

remap = tdu.remap

def _rundelayed(code, delayFrames=1):
	return mod.td.run(code, delayFrames=delayFrames)

class PatternLoader(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.SvgWidth = tdu.Dependency(1)
		self.SvgHeight = tdu.Dependency(1)
		self.patternsettings = None  # type: PatternSettings
		self.patterndata = PatternData()
		_rundelayed('op({!r}).LoadPattern()'.format(self.ownerComp.path), delayFrames=1)

	def op(self, path):
		return self.ownerComp.op(path)

	@property
	def _rawShapes(self):
		return self.op('raw_shapes')

	@property
	def PatternJsonFileName(self):
		return self._GetPatternFileName('json')

	def _GetPatternFileName(self, ext):
		svgname = self.ownerComp.par.Svgfile.eval()
		if not svgname or not svgname.endswith('.svg'):
			return None
		return svgname.replace('.svg', '.' + ext)

	@loggedmethod
	def LoadPattern(self):
		self.patterndata = PatternData()
		svgxmlop = self.op('svg_xml')
		svgxmlop.par.loadonstartpulse.pulse()
		svgxml = svgxmlop.text
		self._LoadPatternSettings()
		self.patterndata.addGroupShapeStates(self.patternsettings.groupshapestates)
		self.patterndata.setDefaultShapeState(self.patternsettings.defaultshapestate)
		self._LoadPatternFromSvg(svgxml)
		sop = self.op('build_geometry')
		self._BuildGroups()
		self._MergeDuplicateShapes()
		self._BuildGeometry(sop)
		self._AssignGeometryGroups(sop)
		self._ApplyDepthLayeringToShapes(sop)
		_rundelayed('op({!r}).ForceTableCooks()'.format(self.ownerComp.path), delayFrames=1)

	@loggedmethod
	def ForceTableCooks(self):
		for o in self.ownerComp.ops(
				'build_shape_attr_table',
				'build_shape_group_sequence_indices',
				'build_group_table',
				'build_sequence_step_table',
				'build_group_default_shape_states',
				'build_shape_default_states',
		):
			o.cook(force=True)

	@simpleloggedmethod
	def _LoadPatternFromSvg(self, svgxml):
		parser = _SvgParser(self, self.patternsettings)
		parser.parse(svgxml)
		self.SvgWidth.val = parser.svgwidth
		self.SvgHeight.val = parser.svgheight
		self.patterndata.addShapes(parser.shapes)

	@loggedmethod
	def _BuildGeometry(self, sop):
		sop.clear()
		sop.primAttribs.create('Cd')
		sop.primAttribs.create('shapeIndex', 0)
		sop.primAttribs.create('duplicate', 0)
		# distance around path (absolute), distance around path (relative to shape length)
		sop.vertexAttribs.create('absRelDist', (0.0, 0.0))
		for shape in self.patterndata.shapes:
			# if shape.isduplicate:
			# 	continue
			poly = sop.appendPoly(len(shape.points), addPoints=True, closed=False)
			poly.shapeIndex[0] = shape.shapeindex
			poly.duplicate[0] = int(shape.isduplicate)
			if shape.color:
				poly.Cd[0] = shape.color[0] / 255.0
				poly.Cd[1] = shape.color[1] / 255.0
				poly.Cd[2] = shape.color[2] / 255.0
			else:
				poly.Cd[0] = poly.Cd[1] = poly.Cd[2] = 1
			poly.Cd[3] = 1
			for i, pathpt in enumerate(shape.points):
				vertex = poly[i]
				vertex.point.x = pathpt.pos[0]
				vertex.point.y = pathpt.pos[1]
				vertex.point.z = pathpt.pos[2]
				vertex.absRelDist[0] = pathpt.absdist
				vertex.absRelDist[1] = pathpt.reldist

	@loggedmethod
	def _AssignGeometryGroups(self, sop):
		for group in self.patterndata.groups:
			primgroup = sop.primGroups.get(group.groupname)
			if primgroup is None:
				sop.createPrimGroup(group.groupname)
				primgroup = sop.primGroups[group.groupname]
			for shapeindex in group.shapeindices:
				primgroup.add(sop.prims[shapeindex])

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
			poly.duplicate[0] = srcpoly.duplicate[0]
			for vertex in poly:
				srcvertex = srcpoly[vertex.index]
				vertex.point.x = srcvertex.point.x
				vertex.point.y = srcvertex.point.y
				vertex.point.z = srcvertex.point.z
				_copyAttrVals(toattr=vertex.absRelDist, fromattr=srcvertex.absRelDist)
				_copyAttrVals(toattr=vertex.uv, fromattr=srcvertex.uv)
				_copyAttrVals(toattr=vertex.centerPos, fromattr=srcvertex.centerPos)
		for g in sop.primGroups.values():
			g.destroy()
		self._AssignGeometryGroups(sop)

	@loggedmethod
	def BuildGroupTable(self, dat):
		dat.clear()
		dat.appendRow([
			'groupname',
			'grouppath',
			'inferencetype',
			'inferredfromvalue',
			'depthlayer',
			'depth',
			'sequencelength',
			'shapecount',
			'shapes',
		])
		for groupinfo in self.patterndata.groups:
			dat.appendRow([
				groupinfo.groupname or '',
				groupinfo.grouppath or '',
				groupinfo.inferencetype or '',
				groupinfo.inferredfromvalue if groupinfo.inferredfromvalue is not None else '',
				formatValue(groupinfo.depthlayer, nonevalue=''),
				formatValue(groupinfo.depth, nonevalue=''),
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
		if not self.patterndata.groups:
			return
		for groupinfo in self.patterndata.groups:
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
			'depthlayer',
			'istriangle', 'dupcount', 'radius',
		])
		for shape in self.patterndata.shapes:
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
			dat[r, 'depthlayer'] = formatValue(shape.depthlayer, nonevalue='')
			dat[r, 'istriangle'] = formatValue(int(shape.istriangle))
			dat[r, 'dupcount'] = formatValue(shape.dupcount)
			dat[r, 'radius'] = formatValue(shape.radius)

	# Build a chop with a channel for each group and a sample for each shape.
	# For each sample and group, the value is either the sequenceIndex, or -1 if the shape
	# is not in that group.
	@loggedmethod
	def BuildShapeGroupSequenceIndices(self, chop):
		chop.clear()
		numshapes = len(self.patterndata.shapes)
		chop.numSamples = numshapes
		if not self.patterndata.groups:
			return
		for group in self.patterndata.groups:
			chan = chop.appendChan(group.groupname)
			shapesteps = [-1] * numshapes
			for step in group.sequencesteps:
				for shapeindex in step.shapeindices:
					if shapesteps[shapeindex] == -1:
						shapesteps[shapeindex] = step.sequenceindex
			for shapeindex in range(numshapes):
				chan[shapeindex] = shapesteps[shapeindex]

	@loggedmethod
	def _LoadPatternSettings(self):
		jsondat = self.op('load_json_file')
		jsondat.clear()
		jsondat.par.loadonstartpulse.pulse()
		obj = json.loads(jsondat.text) if jsondat.text else {}
		self.patternsettings = PatternSettings.FromJsonDict(obj)

	@loggedmethod
	def _BuildGroups(self):
		if not self.patternsettings:
			self._LoadPatternSettings()
		generators = GroupGenerators(
			hostobj=self,
			context=self.patterndata,
			patternsettings=self.patternsettings)
		if self.patternsettings.autogroup in (None, True):
			generators.extractInferredGroups()
		generators.runGenerators()
		generators.applyDepthLayering()
		generators.cleanTemporaryGroups()

	@loggedmethod
	def _MergeDuplicateShapes(self):
		merger = _ShapeDeduplicator(self, self.patterndata, self.patternsettings)
		merger.MergeDuplicates()

	@loggedmethod
	def _ApplyDepthLayeringToShapes(self, sop):
		if not self.patternsettings:
			self._LoadPatternSettings()
		layeringspec = self.patternsettings.depthlayering or DepthLayeringSpec()
		for group in self.patterndata.groups:
			if group.depthlayer is None:
				continue
			for shapeindex in group.shapeindices:
				shape = self.patterndata.getShapeByIndex(shapeindex)
				if shape.depthlayer == group.depthlayer:
					continue
				if shape.depthlayer is not None:
					self._LogEvent('Conflicting layers for shape {}: {} != {}'.format(
						shapeindex, shape.depthlayer, group.depthlayer))
					continue
				shape.depthlayer = group.depthlayer
				shape.center[2] = group.depth

		defaultlayer = layeringspec.defaultlayer
		layerdist = layeringspec.layerdistance or 0.1
		for shape in self.patterndata.shapes:
			if shape.depthlayer is None:
				shape.depthlayer = defaultlayer
				if defaultlayer is not None:
					shape.center[2] = defaultlayer * layerdist
			poly = sop.prims[shape.shapeindex]
			z = shape.center[2]
			for vertex in poly:
				vertex.point.z = z

	# def GetDepthForShape(self, shapeindex: int):
	# 	if shapeindex is None or shapeindex < 0 or shapeindex >= len(self.shapes):
	# 		return 0
	# 	return self.shapes[shapeindex].center[2]

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

	@loggedmethod
	def BuildShapeDefaultStateTable(self, dat):
		builder = ShapeStatesBuilder(self, dat)
		builder.Build(self.patterndata)

	@loggedmethod
	def ExportTox(self, name=None, filename=None):
		if not name:
			svgfilepath = pathlib.Path(self.ownerComp.par.Svgfile.eval())
			name = svgfilepath.stem
			if not filename:
				filename = self._GetPatternFileName('tox')
			if not filename:
				return
		holder = self.op('export_holder')
		for o in holder.ops('*'):
			o.destroy()
		template = self.ownerComp.par.Patterndeftemplate.eval()
		self._LogEvent('name: {!r}'.format(name))
		self._LogEvent('template: {!r}'.format(template))
		comp = holder.copy(template, name=name)
		for srcname in [
			'shapes',
			'shape_panels',
			'shape_attrs',
			'shape_group_sequence_indices',
			'path_position_lookup',
			'default_shape_state_table',
			'groups',
			'sequence_steps',
			'shape_attr_table',
		]:
			destname = 'set_' + srcname
			self._LogEvent('copying from {} to {}'.format(srcname, destname))
			dest = comp.op(destname)
			src = self.op(srcname)
			self._LogEvent('src: {!r}'.format(src))
			self._LogEvent('dest: {!r}'.format(dest))
			dest.copy(src)
			dest.lock = True
		if not filename:
			filename = name + '.tox'
		comp.par.externaltox.expr = '{!r} if mod.os.path.exists({!r}) else ""'.format(filename, filename)
		comp.save(filename)

class _SvgParser(LoggableSubComponent):
	def __init__(self, hostobj, settings: PatternSettings):
		super().__init__(hostobj=hostobj, logprefix='SvgParser')
		self.svgwidth = 0
		self.svgheight = 0
		self.scale = 1
		self.offset = tdu.Vector(0, 0, 0)
		self.shapes = []  # type: List[ShapeInfo]
		self.minbound = tdu.Vector(0, 0, 0)
		self.maxbound = tdu.Vector(0, 0, 0)
		self.settings = settings

	def parse(self, svgxml):
		if not svgxml:
			return
		root = ET.fromstring(svgxml)
		self.svgwidth = float(root.get('width', 1))
		self.svgheight = float(root.get('height', 1))
		self.scale = 1 / max(self.svgwidth, self.svgheight)
		self.offset = tdu.Vector(-self.svgwidth / 2, -self.svgheight / 2, 0)
		self._handleElem(root, 0, namestack=[])
		if not self.shapes:
			return
		minbounds = [shape.minbound for shape in self.shapes]
		self.minbound = tdu.Vector(
			min(b.x for b in minbounds),
			min(b.y for b in minbounds),
			min(b.z for b in minbounds))
		maxbounds = [shape.maxbound for shape in self.shapes]
		self.maxbound = tdu.Vector(
			max(b.x for b in maxbounds),
			max(b.y for b in maxbounds),
			max(b.z for b in maxbounds))
		if self.settings.recenter:
			self._recenterCoords()
		if self.settings.rescale:
			self._rescaleCoords()
		self._calculateShapeCenters()
		self._calculateShapeRadiuses()

	def _getShapeByName(self, shapename: str):
		for shape in self.shapes:
			if shape.shapename == shapename:
				return shape
		return None

	def _recenterCoords(self):
		if isinstance(self.settings.recenter, str):
			shapenames = self.settings.recenter.split(' ')
			centershapes = []
			for shapename in shapenames:
				centershape = self._getShapeByName(shapename)
				if centershape:
					centershapes.append(centershape)
			if not centershapes:
				self._LogEvent('Unable to find shape for recentering: {!r}'.format(self.settings.recenter))
				return
			for centershape in centershapes:
				self._calculateShapeCenter(centershape)
			self._LogEvent('Recentering based on shapes: {}'.format(centershapes))
			center = tdu.Vector(averagePoints([centershape.center for centershape in centershapes]))
		else:
			center = tdu.Vector(averagePoints([self.minbound, self.maxbound]))
		for shape in self.shapes:
			for point in shape.points:
				point.pos = list(tdu.Vector(point.pos) - center)

	def _rescaleCoords(self):
		size = self.maxbound - self.minbound
		scale = 1 / max(size.x, size.y, size.z)
		for shape in self.shapes:
			for point in shape.points:
				point.pos = list(tdu.Vector(point.pos) * scale)

	def _calculateShapeCenter(self, shape: ShapeInfo):
		if shape.istriangle and self.settings.fixtrianglecenters:
			self._LogEvent('Shape has is triangle, attempting to fix triangle center')
			try:
				shape.calculateTriangleCenter()
				self._LogEvent('Successfully calculated triangle center for shape: {}'.format(shape))
			except Exception as e:
				self._LogEvent('WARNING: unable to calculate triangle center for shape {} {}'.format(e, shape))
				shape.calculateCenter()
		else:
			# if self.settings.fixtrianglecenters:
			# 	self._LogEvent('Shape is not a triangle, NOT attempting to fix triangle center')
			shape.calculateCenter()

	@loggedmethod
	def _calculateShapeCenters(self):
		for shape in self.shapes:
			self._calculateShapeCenter(shape)

	@loggedmethod
	def _calculateShapeRadiuses(self):
		for shape in self.shapes:
			shape.calculateRadius()

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
			self._LogEvent('Skipping element: {}...'.format(ET.tostring(elem)[:30]))
			return
		if elem.get('display') == 'none':
			self._LogEvent('Skipping element: {}...'.format(ET.tostring(elem)[:30]))
			return
		tagname = _localName(elem.tag)
		if tagname == 'path':
			try:
				self._handlePathElem(elem, elemname=elemname, namestack=namestack)
			except Exception as e:
				self._LogEvent('Skipping element with invalid svg path (namestack: {}, error: {})'.format(namestack, e))
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
		pointpositions = [_pathPoint(firstsegment.start)]
		for segment in path[1:]:
			if isinstance(segment, (svgpath.CubicBezier, svgpath.QuadraticBezier)):
				self._LogEvent('WARNING: treating bezier as line {}...'.format(rawpath[0:20]))
			elif not isinstance(segment, svgpath.Line):
				raise Exception('Unsupported path (can only contain Line after first segment) {} {}'.format(
					type(segment), rawpath))
			pathpt = _pathPoint(segment.end)
			pointpositions.append(pathpt)
		# if pointpositions[-1] == pointpositions[0]:
		# 	pointpositions.pop()
		totaldist = path.length()
		distances = _segmentDistances(path, self.scale)
		totaldist *= self.scale
		self.shapes.append(ShapeInfo(
			shapeindex=len(self.shapes),
			shapename=pathelem.get('id', None),
			shapepath='/'.join(namestack + [elemname]),
			parentpath='/'.join(namestack),
			color=_getPathElementColor(pathelem),
			shapelength=totaldist,
			points=[
				PointData(
					pos=list((pos + self.offset) * self.scale),
					absdist=distances[i],
					reldist=distances[i] / totaldist
				)
				for i, pos in enumerate(pointpositions)
			],
		))

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

def _parseTolerance(value: Union[bool, float, int]):
	if value is None:
		return None
	if isinstance(value, bool):
		return 0.0 if value else None
	return float(value)

class _ShapeIndexRemapper(LoggableSubComponent):
	def __init__(self, hostobj, logprefix='ShapeRemap'):
		super().__init__(hostobj, logprefix=logprefix)
		self.oldtonewindex = {}  # type: Dict[int, int]

	def __getitem__(self, oldindex):
		return self.oldtonewindex.get(oldindex)

	def __setitem__(self, oldindex, newindex):
		self.oldtonewindex[oldindex] = newindex

	def __contains__(self, oldindex):
		return oldindex in self.oldtonewindex

	def __len__(self):
		return len(self.oldtonewindex)

	def __bool__(self):
		return bool(self.oldtonewindex)

	@loggedmethod
	def RemapShapesInGroups(self, patterndata: PatternData):
		modified = False
		for group in patterndata.groups:
			if self._RemapShapesInGroup(group):
				modified = True
		return modified

	def _RemapShapesInGroup(self, group: GroupInfo):
		modified = _ReplaceIndices(group.shapeindices, self.oldtonewindex)
		for step in group.sequencesteps:
			if _ReplaceIndices(step.shapeindices, self.oldtonewindex):
				modified = True
		if modified:
			self._LogEvent('Replaced indices in group {}'.format(group.groupname))
		else:
			self._LogEvent('No changes in group {}'.format(group.groupname))
		return modified

class _ShapeDeduplicator(LoggableSubComponent):
	def __init__(self, hostobj, patterndata: PatternData, patternsettings: PatternSettings):
		super().__init__(hostobj, logprefix='ShapeDedup')
		self.patterndata = patterndata
		self.dupremapper = _ShapeIndexRemapper(self, 'DeDup')
		self.tolerance = _parseTolerance(patternsettings.mergedups)

	@loggedmethod
	def MergeDuplicates(self):
		if self.tolerance is None:
			return
		self._LoadDuplicates()
		self._LogEvent('Found {} shapes to replace'.format(len(self.dupremapper)))
		if self.dupremapper:
			self.dupremapper.RemapShapesInGroups(self.patterndata)
			self._RemoveDuplicateShapes()

	def _LoadDuplicates(self):
		for i, shape1 in enumerate(self.patterndata.shapes):
			if shape1.shapeindex in self.dupremapper:
				continue
			dupsforshape = []
			for shape2 in self.patterndata.shapes[i + 1:]:
				if shape2.isEquivalentTo(shape1, self.tolerance):
					self.dupremapper[shape2.shapeindex] = shape1.shapeindex
					dupsforshape.append(shape2.shapeindex)
					shape2.dupcount = -1
			shape1.dupcount = len(dupsforshape)
			if shape1.dupcount > 1:
				self._LogEvent('Found duplicates for shape {}: {}'.format(shape1.shapeindex, dupsforshape))
			# else:
			# 	self._LogEvent('No duplicates found for shape {}'.format(shape1.shapeindex))

	def _RemoveDuplicateShapes(self):
		self._LogEvent('Removing {} duplicate shapes'.format(len(self.dupremapper)))
		remainingshapes = []
		removedshapecount = 0
		resequencer = _ShapeIndexRemapper(self, 'ReSeq')
		for shape in self.patterndata.shapes:
			if shape.isduplicate:
				removedshapecount += 1
			else:
				oldindex = shape.shapeindex
				shape.shapeindex = len(remainingshapes)
				remainingshapes.append(shape)
				if shape.shapeindex != oldindex:
					resequencer[oldindex] = shape.shapeindex
		if not resequencer:
			self._LogEvent('No resequencing changes needed')
			return False
		self._LogEvent('Removing {} shapes, {} remaining'.format(removedshapecount, len(remainingshapes)))
		self.patterndata.shapes = remainingshapes
		resequencer.RemapShapesInGroups(self.patterndata)

def _ReplaceIndices(indexlist: List[int], replacements: Dict[int, int]):
	if not indexlist:
		return False
	newlist = []
	modified = False
	for index in indexlist:
		if index not in replacements:
			newlist.append(index)
		else:
			newindex = replacements[index]
			if newindex not in newlist:
				newlist.append(newindex)
			modified = True
	if not modified:
		return False
	newlist.sort()
	indexlist[:] = newlist
	return True
