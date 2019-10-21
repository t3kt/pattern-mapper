from typing import Any, Dict, List, Iterable

from .common import LoggableSubComponent, ExtensionBase
from .common import cleandict, mergedicts, parseValue, formatValue
from pattern_model import ShapeState, PatternData, TransformSpec, TextureLayer

if False:
	from ._stubs import *

print('pattern_state.py loading...')

class _ParGroup:
	def __init__(self, o, switchparname: str, *parnames: str, haschannels=True):
		self.switchpar = getattr(o.par, switchparname.capitalize()) if switchparname else None
		self.parnames = list([p.capitalize() for p in parnames])
		self.pars = o.pars(*parnames)
		self.tuplenames = list({p.tupletName for p in self.pars})
		self.haschannels = haschannels

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
				val = obj[p.name]
				if hasattr(val, 'val'):
					pass
				p.val = obj[p.name]
				matchedany = True
		if matchedany:
			self.switchpar.val = True
		elif clearmissing:
			self.switchpar.val = False

	def addRows(self, dat, filtered=True, menuindices=False, blanks=False, switches=False):
		if switches:
			dat.appendRow([self.switchpar.name, int(self.switchpar)])
		if not self.isactive:
			if filtered:
				return
			if blanks:
				for p in self.pars:
					dat.appendRow([p.name, ''])
				return
		for p in self.pars:
			if p.isToggle:
				val = int(p)
			elif p.isMenu and menuindices:
				val = p.menuIndex
			else:
				val = formatValue(p.eval())
			dat.appendRow([p.name, val])

	def readRows(self, dat, column, clearmissing=True):
		vals = {}
		for p in self.pars:
			cell = dat[p.name, column]
			val = parseValue(cell.val) if cell is not None else None
			if val is not None:
				vals[p.name] = val
		self.setVals(vals, clearmissing=clearmissing)

	@classmethod
	def ForTransformSpec(cls, o, switchparname: str, prefix: str):
		return cls(o, switchparname, *TransformSpec.AllParamNames(prefix))

	@classmethod
	def ForTextureLayer(cls, o, switchparname: str, prefix: str):
		return cls(o, switchparname, *TextureLayer.AllParamNames(prefix))

class _SettingsEditor(ExtensionBase):
	def __init__(self, ownerComp, pargroups: List[_ParGroup]):
		super().__init__(ownerComp)
		self.par = ownerComp.par
		self.pargroups = list(pargroups or [])
		self.UpdateParStates()

	def UpdateParStates(self):
		for pg in self.pargroups:
			pg.updateParsEnabled()

	def GetStateDict(self, filtered=True, channelsonly=True):
		return cleandict(mergedicts(*[
			pg.getVals(filtered=filtered)
			for pg in self.pargroups
			if pg.haschannels or not channelsonly
		]))

	def SetStateDict(self, obj: Dict[str, Any], clearmissing=True):
		for pg in self.pargroups:
			pg.setVals(obj, clearmissing=clearmissing)

	def GetState(self, filtered=True, channelsonly=True):
		return self.GetStateDict(filtered=filtered, channelsonly=channelsonly)

	def SetState(self, state, clearmissing=True):
		self.SetStateDict(state, clearmissing=clearmissing)

	def BuildStateTable(self, dat, filtered=True, menuindices=False, blanks=False, switches=False):
		dat.clear()
		for pg in self.pargroups:
			pg.addRows(dat, filtered=filtered, menuindices=menuindices, blanks=blanks, switches=switches)

	def ReadStateRows(self, dat, column=1, clearmissing=True):
		for pg in self.pargroups:
			pg.readRows(dat, column, clearmissing=clearmissing)

	def _GetActiveGroups(self, channelsonly=True):
		for pg in self.pargroups:
			if channelsonly and not pg.haschannels:
				continue
			if pg.isactive:
				yield pg

	def GetActiveNames(self, channelsonly=True):
		names = []
		for pg in self._GetActiveGroups(channelsonly):
			names += pg.parnames
		return names

	def GetActiveTupleNames(self, channelsonly=True):
		names = []
		for pg in self._GetActiveGroups(channelsonly):
			names += pg.tuplenames
		return names

class ShapeSettingsEditor(_SettingsEditor):
	def __init__(self, ownerComp):
		o = ownerComp
		super().__init__(ownerComp, [
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
		])


class ShapeStateEditor(_SettingsEditor):
	def __init__(self, ownerComp):
		o = ownerComp
		# ShapeState.CreatePars(o)
		self._groupnamepargroup = _ParGroup(o, 'Isgroup', 'Group', haschannels=False)
		super().__init__(
			ownerComp,
			[
				_ParGroup(o, 'Includepathvisible', 'Pathvisible'),
				_ParGroup(o, 'Includepanelvisible', 'Panelvisible'),
				_ParGroup(o, 'Includepathcolor', 'Pathcolor[rgba]'),
				_ParGroup(o, 'Includepanelcolor', 'Panelcolor[rgba]'),
				_ParGroup.ForTransformSpec(o, 'Includelocaltransform', 'Local'),
				_ParGroup.ForTransformSpec(o, 'Includeglobaltransform', 'Global'),
				_ParGroup.ForTextureLayer(o, 'Includepathtex', 'Pathtex'),
				_ParGroup.ForTextureLayer(o, 'Includetexlayer1', 'Texlayer1'),
				_ParGroup.ForTextureLayer(o, 'Includetexlayer2', 'Texlayer2'),
				self._groupnamepargroup,
			]
		)

	def GetState(self, filtered=True, channelsonly=True) -> ShapeState:
		obj = self.GetStateDict(filtered=filtered, channelsonly=channelsonly)
		return ShapeState.FromParamsDict(obj)

	def SetState(self, state: ShapeState, clearmissing=True):
		obj = state.ToParamsDict()
		self.SetStateDict(obj, clearmissing=clearmissing)

	def SetStateDict(self, obj: Dict[str, Any], clearmissing=True):
		super().SetStateDict(obj, clearmissing=clearmissing)
		self.par.Global = not obj.get('Group')


class ShapeStatesBuilder(LoggableSubComponent):
	def __init__(self, hostobj, dat):
		super().__init__(hostobj=hostobj, logprefix='ShapeStatesBuilder')
		self.dat = dat

	def Build(self, patterndata: PatternData):
		self.dat.clear()
		self.dat.appendRow(ShapeState.AllParamNames())
		if patterndata is None:
			return
		n = len(patterndata.shapes)
		self.dat.setSize(1 + n, self.dat.numCols)

	def _AddStates(self, shapestate: ShapeState, shapeindices: Iterable[int]):
		obj = shapestate.ToParamsDict()
		self._LogEvent('OMG state params: {!r}'.format(obj))
		for shapeindex in shapeindices:
			for key, val in obj.items():
				self.dat[shapeindex + 1, key] = val

def BuildShapeStateChannels(chop, shapestate: ShapeState):
	chop.clear()
	if not shapestate:
		return
	parvals = shapestate.ToParamsDict()
	for name in sorted(parvals.keys()):
		val = parvals[name]
		chan = chop.appendChan(name)
		chan[0] = val

def BuildChannelAttributeTable(dat: DAT, attrs: DAT, prefixes: List[str]):
	dat.clear()
	if not prefixes:
		prefixes = ['']
	for prefix in prefixes:
		for srcrow in attrs.rows():
			vals = _padList(srcrow, 4, default='')
			dat.appendRow([
				(prefix + val) if val and val != '_' else '_'
				for val in vals
			])

def _padList(vals, length, default=None):
	return [
		vals[i] if vals and i < len(vals) else default
		for i in range(length)
	]
