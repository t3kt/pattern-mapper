from collections import defaultdict
from io import StringIO
from typing import DefaultDict, List

if False:
	from .common.lib._stubs import *

# adds the 'packages/' dir to the import path
import td_python_package_init
td_python_package_init.init()

import svg.path as svgpath
import svg.svg as svg

import xml.etree.ElementTree as ET

remap = mod.tdu.remap

def getGroupChanNames(groupspec):
	if not groupspec:
		return []
	if ' ' not in groupspec:
		return ['group_' + groupspec]
	return ['group_' + part for part in groupspec.split(' ')]

def generateSequenceIndex(chop, shapeattrs, mask, sortby):
	chop.clear()
	seqindex = chop.appendChan('seqindex')
	n = chop.numSamples = shapeattrs.numSamples
	sortby = sortby or 'index'
	sortchan = shapeattrs.chan(sortby)
	maskchan = mask['mask']
	if sortchan is None:
		for i in range(n):
			seqindex[i] = i / (n - 1)
	else:
		sortvals = []
		for i in range(n):
			if maskchan[i] < 0.5:
				seqindex[i] = 0
				continue
			s = sortchan[i]
			if s not in sortvals:
				sortvals.append(s)
		if len(sortvals) < 2:
			return
		sortvals.sort()
		for sortvalindex, sortval in enumerate(sortvals):
			for shapeindex in range(n):
				if sortchan[shapeindex] == sortval and maskchan[shapeindex] >= 0.5:
					seqindex[shapeindex] = sortvalindex / (len(sortvals) - 1)

class SequenceStep:
	def __init__(
			self,
			sequenceindex=0,
			shapeindices: List[int]=None,
			isdefault=False):
		self.sequenceindex = sequenceindex
		self.shapeindices = list(shapeindices or [])
		self.isdefault = isdefault

class GroupInfo:
	def __init__(
			self,
			groupname,
			groupindex=None,
			shapeindices: List[int]=None,
			sequencesteps: List[SequenceStep]=None,
		):
		self.groupname = groupname
		self.groupindex = groupindex
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])

class PatternParser:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	@property
	def _shapeAttrs(self):
		return self.ownerComp.op('shape_attrs')

	@property
	def _shapes(self):
		return self.ownerComp.op('shapes')

	def BuildGroupsTable(self, dat):
		# yes it's inefficient to build the groupinfos both here and for the
		# steps table, but something about using a CHOP execute to construct
		# the tables seems not great for some reason
		groupinfos = self._BuildGroupInfos()
		dat.clear()
		dat.appendRow(['groupname', 'groupindex', 'sequencelength', 'shapes'])
		for groupinfo in groupinfos:
			dat.appendRow([
				groupinfo.groupname,
				groupinfo.groupindex,
				len(groupinfo.sequencesteps),
				' '.join(map(str, groupinfo.shapeindices)),
			])

	def BuildSequenceStepsTable(self, dat):
		groupinfos = self._BuildGroupInfos()
		dat.clear()
		dat.appendRow(['groupname', 'sequenceindex', 'isdefault', 'shapes'])
		for groupinfo in groupinfos:
			for step in groupinfo.sequencesteps:
				if not step.shapeindices:
					continue
				dat.appendRow([
					groupinfo.groupname,
					step.sequenceindex,
					int(step.isdefault),
					' '.join(map(str, step.shapeindices)),
				])

	def _BuildGroupInfos(self):
		attrs = self._shapeAttrs
		n = attrs.numSamples
		seqindexchan = attrs.chan('sequenceIndex')
		groupinfos = []
		for groupindex, groupchan in enumerate(attrs.chans('group_*')):
			groupinfo = GroupInfo(
				groupname=groupchan.name.replace('group_', ''),
				groupindex=groupindex,
				shapeindices=[i for i in range(n) if groupchan[i]],
			)
			stepsbyindex = _keydefaultdict(lambda i: SequenceStep(i))  # type: DefaultDict[int, SequenceStep]
			if seqindexchan is None:
				stepsbyindex[0] = SequenceStep(isdefault=True, shapeindices=groupinfo.shapeindices)
			else:
				for i in groupinfo.shapeindices:
					seqindex = round(seqindexchan[i])
					stepsbyindex[seqindex].shapeindices.append(i)
			for seqindex in range(max(stepsbyindex.keys())):
				groupinfo.sequencesteps.append(stepsbyindex[seqindex])
			groupinfos.append(groupinfo)
		return groupinfos

	def BuildPathLookupTable(self, chop, tablelength):
		chop.clear()
		shapes = self._shapes
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


class PatternDebugger:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp

	@property
	def _shapeAttrs(self):
		return self.ownerComp.op('shape_attrs')

	@property
	def _shapeCount(self):
		return self._shapeAttrs.numSamples

	def SelectShape(self, i, toggle=False):
		n = self._shapeCount
		if i < 0 or i >= n or (toggle and i == self.ownerComp.par.Selectedshape):
			self.ownerComp.par.Selectedshape = -1
		else:
			self.ownerComp.par.Selectedshape = i

	def PrevShape(self):
		i = self.ownerComp.par.Selectedshape
		if i > 0:
			i -= 1
		else:
			i = self._shapeCount - 1
		self.SelectShape(i)

	def NextShape(self):
		i = self.ownerComp.par.Selectedshape
		n = self._shapeCount
		if i < (n - 1):
			i += 1
		else:
			i = 0
		self.SelectShape(i)

	def BuildShapeInfo(self, dat):
		dat.clear()
		i = self.ownerComp.par.Selectedshape.eval()
		attrs = self._shapeAttrs
		if i == -1 or i >= attrs.numSamples:
			i = None
			dat.appendRow(['index', ''])
		else:
			dat.appendRow(['index', i])
		groups = {}
		vals = {}
		for chan in attrs.chans():
			if chan.name == 'index':
				continue
			if i is None:
				val = ''
			else:
				val = chan[i]
			if chan.name.startswith('group_'):
				groupname = chan.name.replace('group_','')
				groups[groupname] = int(val) if isinstance(val, (float,int)) else val
			elif isinstance(val, str):
				vals[chan.name] = val
			else:
				vals[chan.name] = round(val, 4)
		for name in sorted(vals.keys()):
			dat.appendRow([name, vals[name]])
		for name in sorted(groups.keys()):
			dat.appendRow(['group[{}]'.format(name), groups[name]])

def fixFaceFlipping(sop, insop):
	sop.copy(insop)
	for prim in sop.prims:
		if prim.normal.z < 0:
			origpoints = [v.point for v in prim]
			n = len(prim)
			for i in range(n):
				prim[i].point = origpoints[-i]

def parseSvgPattern(svgxml, sop):
	sop.clear()
	if not svgxml:
		return
	root = ET.fromstring(svgxml)
	for pathelem in root.iter('{http://www.w3.org/2000/svg}path'):
		rawpath = pathelem.attrib['d']
		path = svgpath.parse_path(rawpath)
		if len(path) < 2:
			raise Exception('Unsupported path (too short) {}'.format(rawpath))
		poly = sop.appendPoly(len(path), addPoints=True, closed=path.closed)
		firstsegment = path[0]
		if not isinstance(firstsegment, svgpath.Move):
			raise Exception('Unsupported path (must start with Move) {}'.format(rawpath))
		print('omg new path', rawpath)
		vertex = poly[0]
		pathpt = _pathpoint(firstsegment.start)
		print('... first point:', pathpt)
		vertex.point.x = pathpt[0]
		vertex.point.y = pathpt[1]
		for i, segment in enumerate(path[1:]):
			if not isinstance(segment, svgpath.Line):
				raise Exception('Unsupported path (can only contain Line after first segment) {} {}'.format(
					type(segment), rawpath))
			vertex = poly[i]
			pathpt = _pathpoint(segment.end)
			print('... segment start:', _pathpoint(segment.start), 'end:', _pathpoint(segment.end))
			vertex.point.x, vertex.point.y = pathpt


def _pathpoint(pathpt: complex):
	return pathpt.real, pathpt.imag

def _parseSvgXml(xmltext):
	if not xmltext:
		return None
	f = StringIO(xmltext)
	return svg.Svg(f)

def buildPatternFromSvg(xmltext):
	svgdoc = _parseSvgXml(xmltext)

	pass

class _Shape:
	def __init__(
			self,
			path: svg.Path):
		self.path = path

		pass

def _hextorgb(hexcolor: str):
	if not hexcolor:
		return None
	if hexcolor.startswith('#'):
		hexcolor = hexcolor[1:]
	return _HEXDEC[hexcolor[0:2]], _HEXDEC[hexcolor[2:4]], _HEXDEC[hexcolor[4:6]]

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}


# variant of defaultdict that passes the key to the factory function
# https://stackoverflow.com/questions/2912231/is-there-a-clever-way-to-pass-the-key-to-defaultdicts-default-factory
class _keydefaultdict(defaultdict):
	def __missing__(self, key):
		if self.default_factory is None:
			raise KeyError(key)
		else:
			ret = self[key] = self.default_factory(key)
			return ret
