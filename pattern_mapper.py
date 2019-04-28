# NOTE: THIS IS MOSTLY OBSOLETE

from typing import DefaultDict

from pattern_model import SequenceStep, GroupInfo
try:
	from common import keydefaultdict, hextorgb
except ImportError:
	from lib.common import keydefaultdict, hextorgb

if False:
	from .lib._stubs import *

remap = tdu.remap

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
		dat.appendRow(['groupname', 'sequencelength', 'shapes'])
		for groupinfo in groupinfos:
			dat.appendRow([
				groupinfo.groupname,
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
					int(step.isdefault or 0),
					' '.join(map(str, step.shapeindices)),
				])

	def _BuildGroupInfos(self):
		attrs = self._shapeAttrs
		n = attrs.numSamples
		seqindexchan = attrs.chan('sequenceIndex')
		groupinfos = []
		for groupchan in attrs.chans('group_*'):
			groupinfo = GroupInfo(
				groupname=groupchan.name.replace('group_', ''),
				shapeindices=[i for i in range(n) if groupchan[i]],
			)
			stepsbyindex = keydefaultdict(lambda i: SequenceStep(i))  # type: DefaultDict[int, SequenceStep]
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

	def PrevGroup(self):
		self._StepSelectedGroup(-1)

	def NextGroup(self):
		self._StepSelectedGroup(1)

	def _StepSelectedGroup(self, offset):
		groupnames = [c.val for c in self.ownerComp.op('groups').col('groupname')[1:]]
		grouppar = self.ownerComp.par.Showgroup
		if not groupnames:
			grouppar.val = ''
			return
		if grouppar.eval() not in groupnames:
			index = 0
		else:
			index = (groupnames.index(grouppar.eval()) + offset) % len(groupnames)
		grouppar.val = groupnames[index]
