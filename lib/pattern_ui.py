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


class PatternStatesManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.statetable = self.op('group_shape_states')

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
		pass

	def ClearStates(self):
		self.statetable.clear()
		self.statetable.appendRow(ShapeState.AllParamNames())

	def _GetStateFromRow(self, rowindex: int):
		stateobj = getRowDict(self.statetable, rowindex)
		return ShapeState.FromParamsDict(stateobj)

	def SaveStateToRow(self, state: ShapeState, row: int=None):
		if state is None:
			state = ShapeState()
		stateobj = state.ToParamsDict() or {}
		if row is None:
			addDictRow(self.statetable, stateobj)
		else:
			setDictRow(self.statetable, row, stateobj, clearmissing=True)

	def PromptForNewState(self):
		def _ok(name=None):
			if name is not None:
				self.SaveStateToRow(ShapeState(group=name))
		_ShowPromptDialog(
			title='Create new state',
			text='Enter group name(s) for new state',
			oktext='Create',
			ok=_ok)

	def DeleteStateRow(self, row: int):
		self.statetable.deleteRow(row)


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
