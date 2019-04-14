print('pattern_loader.py loading...')

import xml.etree.ElementTree as ET
from typing import List

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
		self.SvgWidth = tdu.Dependency(0)
		self.SvgHeight = tdu.Dependency(0)

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
			elemid = elem.get('id', '_{}'.format(indexinparent))
			tagname = _localname(elem.tag)
			if tagname == 'path':
				_handlePathElem(elem, parentpath=parentpath)
			else:
				if not parentpath:
					childparentpath = '/'
				else:
					childparentpath = parentpath + '/' + elemid
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
				if not isinstance(segment, svgpath.Line):
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
			n = len(prim)
			for i in range(n):
				prim[i].point = origpoints[-i]

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
