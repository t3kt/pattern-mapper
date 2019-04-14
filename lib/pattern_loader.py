print('pattern_loader.py loading...')

import xml.etree.ElementTree as ET

if False:
	from ._stubs import *

# adds the 'packages/' dir to the import path
import td_python_package_init
td_python_package_init.init()

import svg.path as svgpath

try:
	from common import ExtensionBase, simpleloggedmethod, hextorgb
except ImportError:
	from .common import ExtensionBase, simpleloggedmethod, hextorgb

from pattern_model import GroupInfo, SequenceStep, ShapeInfo

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
		sop.primAttribs.create('shapeid', '')
		sop.primAttribs.create('Cd')
		sop.primAttribs.create('shapelength', 0.0)
		# distance around path (absolute), distance around path (relative to shape length)
		sop.vertexAttribs.create('absreldist', (0.0, 0.0))
		root = ET.fromstring(svgxml)
		self.SvgWidth.val = float(root.attrib['width'])
		self.SvgHeight.val = float(root.attrib['height'])
		scale = 1 / max(self.SvgWidth.val, self.SvgHeight.val)
		offset = -self.SvgWidth.val / 2, -self.SvgHeight.val / 2
		for pathelem in root.iter('{http://www.w3.org/2000/svg}path'):
			rawpath = pathelem.attrib['d']
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
			poly.shapelength[0] = totaldist
			poly.shapeid[0] = pathelem.attrib['id'] if 'id' in pathelem.attrib else ''
			_applyPathColor(poly, pathelem)
			for i, pathpt in enumerate(pathpoints):
				vertex = poly[i]
				vertex.point.x = (pathpt[0] + offset[0]) * scale
				vertex.point.y = -((pathpt[1] + offset[1]) * scale)
				vertex.absreldist[0] = distances[i]
				vertex.absreldist[1] = distances[i] / totaldist

	@staticmethod
	def FixFaceFlipping(sop):
		fixFaceFlipping(sop)


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
	return pathpt.real, pathpt.imag
