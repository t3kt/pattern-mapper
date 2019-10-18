print('pattern_ui.py loading...')

from typing import Callable
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

class PatternStatesManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.statetable = self.op('group_shape_states')
		self.stateeditor = self.op('shape_state_editor')  # type: ShapeStateEditor
		self.statesjson = self.op('states_json')
		self.isloadingstatefromtable = False

	def LoadStates(self):
		dat = self.op('states_json')
		dat.par.loadonstartpulse.pulse()
		jsontext = dat.text
		obj = json.loads(jsontext) if jsontext else {}
		states = PatternStates.FromJsonDict(obj)
		self.ClearStates()
		self.SaveStateToRow(states.defaultshapestate or ShapeState.DefaultState())
		for state in states.groupshapestates:
			self.SaveStateToRow(state)

	def SaveStates(self, filename: str=None):
		states = self._BuildStates()
		statesobj = states.ToJsonDict()
		statesjson = json.dumps(statesobj, indent='  ')
		self.statesjson.text = statesjson
		# TODO: save to file?

	def _BuildStates(self):
		states = PatternStates()
		for row in range(1, self.statetable.numRows):
			state = self._GetStateFromRow(row)
			if not state.group and not states.defaultshapestate:
				states.defaultshapestate = state
			else:
				states.groupshapestates.append(state)
		return states

	def ClearStates(self):
		self.statetable.clear()
		self.statetable.appendRow(['Group', 'JSON'])

	def _GetStateFromRow(self, rowindex: int):
		statename = self.statetable[rowindex, 'Group'] or ''
		statejson = str(self.statetable[rowindex, 'JSON'] or '')
		stateobj = json.loads(statejson) if statejson else {}
		state = ShapeState.FromParamsDict(stateobj)
		state.group = statename
		return state

	def SaveStateToRow(self, state: ShapeState, row: int=None):
		if self.statetable.numRows < 0 or self.statetable.numCols < 2 or self.statetable[0,0] != 'Group' or self.statetable[0, 1] != 'JSON':
			self.ClearStates()
		if state is None:
			state = ShapeState()
		stateobj = state.ToJsonDict() or {}
		statejson = json.dumps(stateobj)
		if row is None or row > (self.statetable.numRows - 1):
			self.statetable.appendRow([state.group or '', statejson])
		else:
			self.statetable[row, 'Group'] = state.group or ''
			self.statetable[row, 'JSON'] = statejson

	def PromptForNewState(self):
		def _ok(name=None):
			if name is not None:
				self.SaveStateToRow(ShapeState(group=name))
		_ShowPromptDialog(
			title='Create new state',
			text='Enter group name(s) for new state',
			oktext='Create',
			ok=_ok)

	def PromptEditStateName(self, row: int=None):
		if row is None:
			row = self._GetSelectedRow()

		def _ok(name=None):
			if name is not None:
				self.RenameStateRow(row, name)
		_ShowPromptDialog(
			title='Edit state',
			text='Enter group name(s) for state',
			oktext='Save',
			ok=_ok)

	def RenameStateRow(self, row: int, name: str):
		print('RenameStateRow(row: {!r}, name: {!r})'.format(row, name))
		self.statetable[row, 'Group'] = name or ''
		if row == self._GetSelectedRow():
			self.stateeditor.par.Isgroup = bool(name)
			self.stateeditor.par.Group = name or ''

	def DeleteStateRow(self, row: int):
		self.statetable.deleteRow(row)

	def OnSelectStateRow(self, row: int):
		state = self._GetStateFromRow(row)
		self.isloadingstatefromtable = True
		try:
			self.stateeditor.SetState(state, True)
			self.stateeditor.par.Isgroup = bool(state.group)
			self.stateeditor.par.Group = state.group or ''
		finally:
			self.isloadingstatefromtable = False

	def OnStateEditorParChange(self, par):
		if self.isloadingstatefromtable:
			return
		state = self.stateeditor.GetState(filtered=True, channelsonly=False)
		row = self._GetSelectedRow()
		self.SaveStateToRow(state, row)

	def _GetSelectedRow(self):
		return int(self.op('iparStatesManager').par.Selectedgroupstateindex) + 1

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
