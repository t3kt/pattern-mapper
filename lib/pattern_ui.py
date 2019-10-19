print('pattern_ui.py loading...')

from typing import Any, Callable, Dict, List, Optional, Union
import json

if False:
	from ._stubs import *
	from ._stubs.PopDialogExt import PopDialogExt

try:
	from common import ExtensionBase
except ImportError:
	from .common import ExtensionBase

try:
	from common import cleandict, excludekeys, mergedicts, addDictRow, getRowDict, setDictRow
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, addDictRow, getRowDict, setDictRow

from pattern_model import ShapeState, PatternStates
from pattern_state import ShapeStateEditor
try:
	from TDStoreTools import DependDict, DependList, StorageManager
except ImportError:
	from _stubs.TDStoreTools import DependDict, DependList, StorageManager

# try:
# 	import _stubs.TDFunctions as TDF
# except ImportError:
# 	TDF = op.TDModules.mod.TDFunctions

class PatternStatesManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.stateeditor = self.op('shape_state_editor')  # type: ShapeStateEditor
		self.statesjson = self.op('states_json')
		self.isloadingstate = False
		self.ipars = self.op('iparStatesManager')

		# TDF.createProperty(
		# 	self,
		# 	'groupstates',
		# 	value=[],
		# 	dependable='deep')
		# if False:
		# 	self.groupstates = DependList()  # type: DependList[DependDict]

	@property
	def groupstates(self):
		states = self.ownerComp.fetch('groupstates', None, search=False)
		if states is None:
			states = DependList()
			self.ownerComp.store('groupstates', states)
		return states

	def LoadStates(self):
		dat = self.op('states_json')
		dat.par.loadonstartpulse.pulse()
		jsontext = dat.text
		obj = json.loads(jsontext) if jsontext else {}
		states = PatternStates.FromJsonDict(obj)
		self.ClearStates()
		self.AddState(states.defaultshapestate or ShapeState.DefaultState())
		for state in states.groupshapestates:
			self.AddState(state)

	def SaveStates(self, filename: str=None):
		states = self._BuildStates()
		statesobj = states.ToJsonDict()
		statesjson = json.dumps(statesobj, indent='  ')
		self.statesjson.text = statesjson
		# TODO: save to file?

	def _BuildStates(self):
		states = PatternStates()
		for state in self.groupstates:
			if not state.group and not states.defaultshapestate:
				states.defaultshapestate = state
			else:
				states.groupshapestates.append(state)
		return states

	def ClearStates(self):
		self.groupstates.clear()

	@property
	def GroupStateCount(self):
		return len(self.groupstates)

	@property
	def GroupStateNames(self):
		return [
			statedict.get('Group', None) or ''
			for statedict in self.groupstates
		]

	@property
	def GroupStateButtonLabels(self):
		return [g or '(default)' for g in self.GroupStateNames]

	def _GetStateDict(self, i: int) -> 'Optional[DependDict[str, Any]]':
		if 0 <= i < self.GroupStateCount:
			return self.groupstates[i]

	def _GetState(self, i: int) -> Optional[ShapeState]:
		statedict = self._GetStateDict(i)
		if statedict is not None:
			return ShapeState.FromParamsDict(statedict)

	def _SetState(self, i: int, state: ShapeState):
		# TODO: bounds check?
		stateobj = state.ToParamsDict()
		self.groupstates[i].val = stateobj

	def AddState(self, nameorstate: Union[str, ShapeState]):
		if isinstance(nameorstate, str):
			state = ShapeState(nameorstate)
		else:
			state = nameorstate
		stateobj = state.ToParamsDict()
		self.groupstates.append(DependDict(**stateobj))

	def PromptForNewState(self):
		def _ok(name=None):
			if name is not None:
				self.AddState(name)
		_ShowPromptDialog(
			title='Create new state',
			text='Enter group name(s) for new state',
			oktext='Create',
			ok=_ok)

	def PromptEditStateName(self, i: int=None):
		if i is None:
			i = self._SelectedIndex

		def _ok(name=None):
			if name is not None:
				self.RenameState(i, name)
		_ShowPromptDialog(
			title='Edit state',
			text='Enter group name(s) for state',
			oktext='Save',
			ok=_ok)

	def RenameState(self, i: int, name: str):
		statedict = self._GetStateDict(i)
		statedict['Group'] = name or ''
		if i == self._SelectedIndex:
			self.stateeditor.SetStateDict({'Group': name or ''}, clearmissing=False)
			self.stateeditor.par.Isgroup = True
			self.stateeditor.par.Group = name or ''

	def DeleteState(self, i: int):
		if 0 <= i < self.GroupStateCount:
			del self.groupstates[i]

	def OnSelectState(self, i: int):
		self.isloadingstate = True
		try:
			statedict = self._GetStateDict(i) or {}
			self.stateeditor.SetStateDict(statedict, clearmissing=True)
			self.stateeditor.par.Isgroup = True
			self.stateeditor.par.Group = statedict.get('Group', None) or ''
		finally:
			self.isloadingstate = False

	def OnStateEditorParChange(self, par):
		if self.isloadingstate:
			return
		statedict = self._SelectedStateDict
		if statedict is None:
			return
		if par.name.startswith('Include'):
			newdict = self.stateeditor.GetStateDict(filtered=True, channelsonly=False)
			statedict.val = newdict
		else:
			statedict[par.name] = par.eval()

	@property
	def _SelectedIndex(self):
		return int(self.ipars.par.Selectedgroupstateindex)

	@_SelectedIndex.setter
	def _SelectedIndex(self, i):
		self.ipars.par.Selectedgroupstateindex = i

	@property
	def _SelectedState(self):
		return self._GetState(self._SelectedIndex)

	@_SelectedState.setter
	def _SelectedState(self, state):
		self._SetState(self._SelectedIndex, state)

	@property
	def _SelectedStateDict(self):
		return self._GetStateDict(self._SelectedIndex)

def _ShowPromptDialog(
		title=None,
		text=None,
		default='',
		textentry=True,
		oktext='OK',
		canceltext='Cancel',
		ok: Callable=None,
		cancel: Callable=None):
	def _callback(info):
		if info['buttonNum'] == 1:
			if ok:
				if not text:
					ok()
				else:
					ok(info.get('enteredText'))
		elif info['buttonNum'] == 2:
			if cancel:
				cancel()
	dialog = op.TDResources.op('popDialog')  # type: PopDialogExt
	dialog.Open(
		title=title,
		text=text,
		textEntry=False if not textentry else (default or ''),
		buttons=[oktext, canceltext],
		enterButton=1, escButton=2, escOnClickAway=True,
		callback=_callback)
