print('pattern_loader.py loading...')

import json
import xml.etree.ElementTree as ET
from typing import List

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
	from common import parseValue, parseValueList, formatValue, formatValueList, ValueRange
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList, ValueRange

from pattern_model import GroupInfo, ShapeInfo, PatternSettings, DepthLayeringSpec, PatternData, ShapeState
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
	def TEMP_jsonObj(self):
		return {
			'groups': GroupInfo.ToJsonDicts(self.patterndata.groups)
		}

	@property
	def PatternJsonFileName(self):
		svgname = self.ownerComp.par.Svgfile.eval()
		if not svgname:
			return ''
		if svgname.endswith('.svg'):
			return svgname.replace('.svg', '.json')
		return ''

	@loggedmethod
	def LoadPattern(self):
		self.patterndata = PatternData()
		svgxmlop = self.op('svg_xml')
		svgxmlop.par.loadonstart.pulse()
		svgxml = svgxmlop.text
		sop = self.op('build_geometry')
		self._LoadPatternSettings()
		self.patterndata.addGroupShapeStates(self.patternsettings.groupshapestates)
		self.patterndata.setDefaultShapeState(self.patternsettings.defaultshapestate)
		self._BuildGeometryFromSvg(sop, svgxml)
		self._BuildGroups()
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
	def _BuildGeometryFromSvg(self, sop, svgxml):
		sop.clear()
		parser = _SvgParser(self, sop)
		parser.parse(
			svgxml,
			recenter=self.ownerComp.par.Recenter,
			rescale=self.ownerComp.par.Rescale)
		self.SvgWidth.val = parser.svgwidth
		self.SvgHeight.val = parser.svgheight
		self.patterndata.addShapes(parser.shapes)

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
			dat[r, 'depthlayer'] = formatValue(shape.shapelength, nonevalue='')

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
			chan = chop.appendChan('seq_' + group.groupname)
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
	def _ApplyDepthLayeringToShapes(self, sop):
		if not self.patternsettings:
			self._LoadPatternSettings()
		layeringspec = self.patternsettings.depthlayering or DepthLayeringSpec()
		for group in self.patterndata.groups:
			if group.depthlayer is None:
				continue
			for shapeindex in group.shapeindices:
				shape = self.patterndata.getShape(shapeindex)
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
	def BuildGroupShapeStateTable(self, dat):
		dat.clear()
		dat.appendRow(['group'] + ShapeState.AllParamNames())
		self.patterndata.defaultshapestate.AddToParamsTable(dat, {'group': '*'})
		for groupshapestate in self.patterndata.groupshapestates:
			groupshapestate.AddToParamsTable(dat)

	@loggedmethod
	def BuildShapeDefaultStateCHOP(self, chop):
		builder = ShapeStatesBuilder(self, chop)
		builder.Build(self.patterndata)

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
			shape.center = [poly.center.x, poly.center.y, poly.center.z]

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
				self._LogEvent('WARNING: treating bezier as line {}...'.format(rawpath[0:20]))
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
