print('pattern_debugger.py loading...')

if False:
	from ._stubs import *

try:
	from common import LoggableSubComponent, ExtensionBase, loggedmethod
except ImportError:
	from .common import LoggableSubComponent, ExtensionBase, loggedmethod

try:
	from common import cleandict, excludekeys, mergedicts
except ImportError:
	from .common import cleandict, excludekeys, mergedicts

try:
	from common import parseValue, parseValueList, formatValue, formatValueList
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList


class PatternDebugger(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)

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
			self.ownerComp.par.Uimode = 'shapes'

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
			if chan.name.startswith('seq_'):
				continue
			if i is None:
				val = ''
			else:
				val = chan[i]
			if chan.name.startswith('group_'):
				groupname = chan.name.replace('group_', '')
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
		self.ownerComp.par.Uimode = 'groups'

	def BuildUIShapeAttrs(self, chop):
		chop.clear()
		mode = self.ownerComp.par.Uimode.eval()
		shapeattrs = self.ownerComp.op('shape_attrs')
		highlight = chop.appendChan('highlight')
		n = shapeattrs.numSamples
		chop.numSamples = n
		if mode == 'shapes':
			selshapeindex = self.ownerComp.par.Selectedshape
			for i in range(n):
				highlight[i] = selshapeindex == -1 or i == selshapeindex
		elif mode == 'groups':
			# seqindices =
			pass

