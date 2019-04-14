print('pattern_loader.py loading...')

from collections import defaultdict
import xml.etree.ElementTree as ET
from typing import DefaultDict, List, Tuple

if False:
	from ._stubs import *

# adds the 'packages/' dir to the import path
import td_python_package_init
td_python_package_init.init()

import svg.path as svgpath

try:
	from common import ExtensionBase, simpleloggedmethod, hextorgb, loggedmethod
except ImportError:
	from .common import ExtensionBase, simpleloggedmethod, hextorgb, loggedmethod

from pattern_model import GroupInfo, SequenceStep, ShapeInfo

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

	@simpleloggedmethod
	def BuildGeometryFromSvg(self, sop, svgxml):
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

		def _handleElem(elem, indexinparent, parentpath=''):
			elemid = elem.get('id')
			if elemid and (elemid == 'Background' or elemid.startswith('-')):
				return
			if elem.get('display') == 'none':
				return
			tagname = _localname(elem.tag)
			if tagname == 'path':
				_handlePathElem(elem, parentpath=parentpath)
			else:
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

		self._BuildInferredGroups(sop)

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
	def BuildInferredGroups(self, dat, sop):
		# NOTE: this depends on `.groups` having been populated already
		if not self.groups:
			self._BuildInferredGroups(sop)
		dat.clear()
		dat.appendRow([
			'groupname',
			'grouppath',
			'inferencetype',
			'inferredfromvalue',
			'sequencelength',
			'shapes',
		])
		for groupinfo in self.groups:
			dat.appendRow([
				groupinfo.groupname,
				groupinfo.grouppath or '',
				groupinfo.inferencetype or '',
				groupinfo.inferredfromvalue if groupinfo.inferredfromvalue is not None else '',
				len(groupinfo.sequencesteps),
				' '.join(map(str, groupinfo.shapeindices)),
			])

	@loggedmethod
	def BuildGroupTable(self, dat):
		if not self.groups:
			self._BuildInferredGroups(sop=self._rawShapes)
		dat.clear()
		dat.appendRow([
			'groupname',
			'grouppath',
			'inferencetype',
			'inferredfromvalue',
			'sequencelength',
			'shapes',
		])
		for groupinfo in self.groups:
			dat.appendRow([
				groupinfo.groupname or '',
				groupinfo.grouppath or '',
				groupinfo.inferencetype or '',
				groupinfo.inferredfromvalue if groupinfo.inferredfromvalue is not None else '',
				len(groupinfo.sequencesteps),
				' '.join(map(str, groupinfo.shapeindices)),
			])

	@loggedmethod
	def BuildSequenceStepTable(self, dat):
		if not self.groups:
			self._BuildInferredGroups(sop=self._rawShapes)
		dat.clear()
		dat.clear()
		dat.appendRow([
			'groupname',
			'sequenceindex',
			'isdefault',
			'inferredfromvalue',
			'shapes',
		])
		for groupinfo in self.groups:
			for step in groupinfo.sequencesteps:
				if not step.shapeindices:
					continue
				dat.appendRow([
					groupinfo.groupname,
					step.sequenceindex,
					int(step.isdefault or 0),
					step.inferredfromvalue,
					' '.join(map(str, step.shapeindices)),
				])

	@loggedmethod
	def AddInferredGroupAttrs(self, sop):
		# NOTE: this depends on `.groups` having been populated already
		if not self.groups:
			self._BuildInferredGroups(sop)
		sop.primAttribs.create('sequenceIndex', 0)
		for group in self.groups:
			attrname = 'group_' + group.groupname
			sop.primAttribs.create(attrname, 0)
			for shapeindex in group.shapeindices:
				getattr(sop.prims[shapeindex], attrname)[0] = 1
			for step in group.sequencesteps:
				for shapeindex in step.shapeindices:
					sop.prims[shapeindex].sequenceIndex[0] = step.sequenceindex

	@loggedmethod
	def _BuildInferredGroups(self, sop):
		shapes = _shapeInfosFromPolys(sop.prims)
		self.groups = _InferredGroupExtractor().load(shapes)

	@staticmethod
	def SetUVLayerToLocalPos(sop, uvlayer: int):
		for prim in sop.prims:
			for vertex in prim:
				vertex.uv[(uvlayer * 3) + 0] = remap(vertex.point.x, prim.min.x, prim.max.x, 0, 1)
				vertex.uv[(uvlayer * 3) + 1] = remap(vertex.point.y, prim.min.y, prim.max.y, 0, 1)

	@staticmethod
	def FixFaceFlipping(sop):
		fixFaceFlipping(sop)

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
			color=(poly.Cd[0], poly.Cd[1], poly.Cd[2]),
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