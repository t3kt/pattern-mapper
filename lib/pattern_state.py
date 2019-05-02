print('pattern_state.py loading...')

from typing import Any, Dict, List, Iterable

if False:
	from ._stubs import *

try:
	from common import LoggableSubComponent, ExtensionBase
except ImportError:
	from .common import LoggableSubComponent, ExtensionBase

try:
	from common import cleandict, excludekeys, mergedicts
except ImportError:
	from .common import cleandict, excludekeys, mergedicts

try:
	from common import parseValue, parseValueList, formatValue, formatValueList
except ImportError:
	from .common import parseValue, parseValueList, formatValue, formatValueList

from pattern_model import ShapeState, PatternData

class ShapeSettingsEditor(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.par = ownerComp.par
		o = ownerComp
		self.pargroups = [
			_ParGroup(o, 'Includepathalpha', 'Pathalpha'),
			_ParGroup(o, 'Includepathoncolor', 'Pathoncolor[rgba]'),
			_ParGroup(o, 'Includepathoffcolor', 'Pathoffcolor[rgba]'),
			_ParGroup(o, 'Includepathphase', 'Pathphase'),
			_ParGroup(o, 'Includepathperiod', 'Pathperiod', 'Pathreverse'),

			_ParGroup(o, 'Includepanelalpha', 'Panelalpha'),
			_ParGroup(o, 'Includepanelcolor', 'Panel*color[rgba]'),

			_ParGroup(o, 'Includepanelglobaltexlevel', 'Panelglobaltexlevel'),
			_ParGroup(o, 'Includepanelglobaluvoffset', 'Panelglobaluvoffset[uvw]'),
			_ParGroup(o, 'Includepanellocaltexlevel', 'Panellocaltexlevel'),
			_ParGroup(o, 'Includepanellocaluvoffset', 'Panellocaluvoffset[uvw]'),

			_ParGroup(o, 'Includelocalscale', 'Localscale[xyz]', 'Localuniformscale'),
			_ParGroup(o, 'Includelocalrotate', 'Localrotate[xyz]'),
			_ParGroup(o, 'Includelocaltranslate', 'Localtranslate[xyz]'),

			_ParGroup(o, 'Includeglobalscale', 'Globalscale[xyz]', 'Globaluniformscale'),
			_ParGroup(o, 'Includeglobalrotate', 'Globalrotate[xyz]'),
			_ParGroup(o, 'Includeglobaltranslate', 'Globaltranslate[xyz]'),
		]
		self.UpdateParStates()

	def UpdateParStates(self):
		for pg in self.pargroups:
			pg.updateParsEnabled()

	def GetState(self, filtered=True):
		return cleandict(mergedicts(*[
			pg.getVals(filtered=filtered)
			for pg in self.pargroups
		]))

	def SetState(self, obj: Dict[str, Any], clearmissing=True):
		for pg in self.pargroups:
			pg.setVals(obj, clearmissing=clearmissing)

	def BuildStateTable(self, dat, filtered=True):
		dat.clear()
		for pg in self.pargroups:
			pg.addRows(dat, filtered=filtered)

	def ReadStateRows(self, dat, column=1, clearmissing=True):
		for pg in self.pargroups:
			pg.readRows(dat, column, clearmissing=clearmissing)

	def GetActiveNames(self):
		names = []
		for pg in self.pargroups:
			if pg.isactive:
				names += pg.parnames
		return names

class _ParGroup:
	def __init__(self, o, switchparname, *parnames):
		self.switchpar = getattr(o.par, switchparname) if switchparname else None
		self.parnames = list(parnames)
		self.pars = o.pars(*parnames)

	def updateParsEnabled(self):
		enabled = self.isactive
		for par in self.pars:
			par.enable = enabled

	@property
	def isactive(self):
		return self.switchpar is None or self.switchpar

	def getVals(self, filtered=False):
		if filtered and not self.isactive:
			return {}
		return {p.name: p.eval() for p in self.pars}

	def setVals(self, obj: Dict[str, Any], clearmissing=True):
		matchedany = False
		for p in self.pars:
			if p.name in obj:
				p.val = obj[p.name]
				matchedany = True
		if matchedany:
			self.switchpar.val = True
		elif clearmissing:
			self.switchpar.val = False

	def addRows(self, dat, filtered=True):
		if filtered and not self.isactive:
			return
		for p in self.pars:
			dat.appendRow([
				p.name,
				p if p.style != 'Toggle' else int(p)
			])

	def readRows(self, dat, column, clearmissing=True):
		vals = {}
		for p in self.pars:
			cell = dat[p.name, column]
			val = parseValue(cell.val) if cell is not None else None
			if val is not None:
				vals[p.name] = val
		self.setVals(vals, clearmissing=clearmissing)


class ShapeStatesBuilder(LoggableSubComponent):
	def __init__(self, hostobj, chop):
		super().__init__(hostobj=hostobj, logprefix='ShapeStatesBuilder')
		self.chop = chop

	def Build(self, patterndata: PatternData):
		self.chop.clear()
		for name in ShapeState.AllParamNames():
			self.chop.appendChan(name)
		if patterndata is None:
			return
		n = len(patterndata.shapes)
		self.chop.numSamples = n
		self._AddStates(patterndata.defaultshapestate, range(n))
		for groupstate in patterndata.groupshapestates:
			shapeindices = patterndata.getShapeIndicesByGroupPattern(parseValueList(groupstate.group))
			self._AddStates(groupstate, shapeindices)

	def _AddStates(self, shapestate: ShapeState, shapeindices: Iterable[int]):
		obj = shapestate.ToParamsDict()
		for shapeindex in shapeindices:
			for key, val in obj.items():
				self.chop[key][shapeindex] = val

