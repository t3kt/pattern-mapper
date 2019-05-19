print('pattern_state.py loading...')

from typing import Any, Dict, List, Iterable, Union

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

try:
	from common import opattrs, createFromTemplate
except ImportError:
	from .common import opattrs, createFromTemplate

from pattern_model import GroupShapeState, ShapeState, PatternData, TransformSpec, TextureLayer

class _ParGroup:
	def __init__(self, o, switchparname: str, *parnames: str, haschannels=True):
		self.switchpar = getattr(o.par, switchparname.capitalize()) if switchparname else None
		self.parnames = list([p.capitalize() for p in parnames])
		self.pars = o.pars(*parnames)
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

	def BuildStateTable(self, dat, filtered=True):
		dat.clear()
		for pg in self.pargroups:
			pg.addRows(dat, filtered=filtered)

	def ReadStateRows(self, dat, column=1, clearmissing=True):
		for pg in self.pargroups:
			pg.readRows(dat, column, clearmissing=clearmissing)

	def GetActiveNames(self, channelsonly=True):
		names = []
		for pg in self.pargroups:
			if channelsonly and not pg.haschannels:
				continue
			if pg.isactive:
				names += pg.parnames
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
				_ParGroup.ForTextureLayer(o, 'Includetexlayer3', 'Texlayer3'),
				_ParGroup.ForTextureLayer(o, 'Includetexlayer4', 'Texlayer4'),
				self._groupnamepargroup,
			]
		)

	def GetState(self, filtered=True, channelsonly=True) -> Union[ShapeState, GroupShapeState]:
		obj = self.GetStateDict(filtered=filtered, channelsonly=channelsonly)
		if (not channelsonly) and self.ownerComp.par.Isgroup:
			state = GroupShapeState.FromParamsDict(obj)
			state.group = self.ownerComp.par.Group.eval()
			return state
		return ShapeState.FromParamsDict(obj)

	def SetState(self, state: ShapeState, clearmissing=True):
		obj = state.ToParamsDict()
		self.SetStateDict(obj, clearmissing=clearmissing)
		if isinstance(state, GroupShapeState):
			self._groupnamepargroup.setVals({'Group': state.group}, clearmissing=clearmissing)
		elif clearmissing:
			self.ownerComp.par.Group = ''
			self.ownerComp.par.Isgroup = False


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
		if patterndata.defaultshapestate:
			self._AddStates(patterndata.defaultshapestate, range(n))
		for groupstate in patterndata.groupshapestates:
			shapeindices = patterndata.getShapeIndicesByGroupPattern(parseValueList(groupstate.group))
			self._AddStates(groupstate, shapeindices)

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

class GroupShapeStateEditorManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)

	@property
	def _Editors(self) -> List[Union[COMP, ShapeStateEditor]]:
		return self.ownerComp.ops('gstate__*')

	def LoadStates(self, groupshapestates: List[GroupShapeState]):
		for editor in self._Editors:
			editor.destroy()
		if not groupshapestates:
			return
		for i, state in enumerate(groupshapestates):
			self._AddStateEditor(state, i)
		pass

	def GetStates(self) -> List[GroupShapeState]:
		return [
			editor.GetState(filtered=True, channelsonly=False)
			for editor in self._Editors
		]

	def _AddStateEditor(self, state: GroupShapeState, index: int):
		editor = createFromTemplate(
			template=self.ownerComp.op('shape_state_editor_template'),
			dest=self.ownerComp,
			name='gstate__{}'.format(index),
			attrs=opattrs(
				nodepos=[200, -500 + (100 * index)])
		)  # type: Union[COMP, ShapeStateEditor]
		editor.SetState(state, clearmissing=True)
		return editor
