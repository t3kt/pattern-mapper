print('pattern_debugger.py loading...')

# noinspection PyUnreachableCode
if False:
	# noinspection PyUnresolvedReferences
	from _stubs import *

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

	def HandleKeyPress(self, key):
		mode = self.ownerComp.par.Uimode
		if key == 'left':
			if mode == 'shapes':
				self.PrevShape()
			elif mode == 'groups':
				self.PrevGroup()
		elif key == 'right':
			if mode == 'shapes':
				self.NextShape()
			elif mode == 'groups':
				self.NextGroup()
		elif key == 'up':
			mode.menuIndex = (mode.menuIndex + 1) % len(mode.menuNames)
		elif key == 'down':
			mode.menuIndex = (mode.menuIndex - 1) % len(mode.menuNames)

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

