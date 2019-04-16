print('pattern_state.py loading...')

from typing import Any, Dict

if False:
	from ._stubs import *

try:
	from common import ExtensionBase
except ImportError:
	from .common import ExtensionBase

try:
	from common import cleandict, excludekeys, mergedicts
except ImportError:
	from .common import cleandict, excludekeys, mergedicts


class ShapeSettingsEditor(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.par = ownerComp.par
		o = ownerComp
		self.pargroups = [
			_ParGroup(o, None, 'Pathalpha'),
			_ParGroup(o, 'Includepathoncolor', 'Pathoncolor[rgba]'),
			_ParGroup(o, 'Includepathoffcolor', 'Pathoffcolor[rgba]'),
			_ParGroup(o, 'Includepanelcolor', 'Panel*color[rgba]'),
			_ParGroup(o, 'Includelocalscale', 'Localscale[xyz]'),
			_ParGroup(o, 'Includelocalrotate', 'Localrotate[xyz]'),
			_ParGroup(o, 'Includelocaltranslate', 'Localtranslate[xyz]'),
			_ParGroup(o, 'Includepathphase', 'Pathphase'),
			_ParGroup(o, 'Includepathperiod', 'Pathperiod', 'Pathreverse'),
		]

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
