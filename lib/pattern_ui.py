from typing import Any, Callable, List, Optional, Union
import json

from .common import ExtensionBase, opattrs, createFromTemplate
from pattern_model import ShapeState, PatternStates
from pattern_state import ShapeStateEditor

if False:
	from ._stubs import *
	from ._stubs.PopDialogExt import PopDialogExt
	from ._stubs.PopMenuExt import PopMenuExt
try:
	from TDStoreTools import DependDict, DependList, StorageManager
except ImportError:
	from _stubs.TDStoreTools import DependDict, DependList, StorageManager

# try:
# 	import _stubs.TDFunctions as TDF
# except ImportError:
# 	TDF = op.TDModules.mod.TDFunctions

print('pattern_ui.py loading...')

class PatternStatesManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.stateeditor = self.op('shape_state_editor')  # type: ShapeStateEditor
		self.statesjson = self.op('states_json')
		self.grouptable = self.op('groups')
		self.statechain = self.op('state_gen_chain')
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
		for statedict in self.groupstates:
			state = ShapeState.FromParamsDict(statedict)
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
		if self._IsValidIndex(i):
			return self.groupstates[i]

	def _IsValidIndex(self, i: int):
		return i is not None and 0 <= i < self.GroupStateCount

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
		statedict = self._GetStateDict(i)
		if statedict is None:
			return

		def _ok(name=None):
			if name is not None:
				self.RenameState(i, name)
		_ShowPromptDialog(
			title='Edit state',
			text='Enter group name(s) for state',
			default=statedict.get('Group') or '',
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

	def OpenStateContextMenu(self, stateButton):
		i = stateButton.digits
		if not self._IsValidIndex(i):
			return
		menuitems = [
			MenuItem(
				'Rename',
				callback=lambda: self.PromptEditStateName(i)),
			MenuItem(
				'Delete',
				callback=lambda: self.DeleteState(i))
		]
		menus.fromButton(stateButton).Show(
			menuitems,
			autoClose=True,
		)

	def _AddStateChainStep(self, i: int):
		state = self._GetState(i)
		statecomp = createFromTemplate(
			self.op('state_template'),
			self.statechain,
			'state__{}'.format(i),
			opattrs(nodepos=[200, 500 - (i * 200)])
		)
		stateeditor = statecomp.op('editor')  # type: ShapeStateEditor
		stateeditor.SetState(state, clearmissing=True)
		if i == 0:
			srcpath = '../in1'
		else:
			srcpath = '../state__{}/out1'.format(i - 1)
		statecomp.op('./sel_input').par.chop = srcpath
		self.statechain.op('./sel_output').par.chop = statecomp.op('./out1')

	def _BuildStateChain(self):
		for o in self.statechain.ops('state__*'):
			o.destroy()
		for i in range(self.GroupStateCount):
			self._AddStateChainStep(i)

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


class MenuItem:
	def __init__(
			self,
			text,
			disabled=False,
			dividerafter=False,
			highlighted=False,
			checked=None,
			hassubmenu=False,
			callback=None):
		self.text = text
		self.disabled = disabled
		self.dividerafter = dividerafter
		self.highlighted = highlighted
		self.checked = checked
		self.hassubmenu = hassubmenu
		self.callback = callback

def ParToggleItem(
		par,
		text=None,
		callback=None,
		**kwargs):
	def _callback():
		par.val = not par
		if callback:
			callback()
	return MenuItem(
		text or par.label,
		checked=par.eval(),
		callback=_callback,
		**kwargs)

def ParEnumItems(par):
	def _valitem(value, label):
		return MenuItem(
			label,
			checked=par == value,
			callback=lambda: setattr(par, 'val', value))
	return [
		_valitem(v, l)
		for v, l in zip(par.menuNames, par.menuLabels)
	]

def ViewOpItem(
		o: 'OP',
		text,
		unique=True,
		borders=True,
		**kwargs):
	return MenuItem(
		text,
		callback=lambda: o.openViewer(unique=unique, borders=borders),
		**kwargs)

class MenuDivider:
	pass

def _PreprocessItems(rawitems: List[Union[MenuItem, MenuDivider]]):
	if not rawitems:
		return []
	processeditems = []
	previtem = None
	for item in rawitems:
		if not item:
			continue
		if isinstance(item, MenuDivider):
			if previtem:
				previtem.dividerafter = True
			previtem = None
		else:
			previtem = item
			processeditems.append(item)
	return processeditems


class _MenuOpener:
	def __init__(self, applyPosition):
		self.applyPosition = applyPosition

	def Show(
			self,
			items: List[Union[MenuItem, MenuDivider]],
			callback=None,
			callbackDetails=None,
			autoClose=None,
			rolloverCallback=None,
			allowStickySubMenus=None):
		items = _PreprocessItems(items)
		if not items:
			return

		popmenu = _getPopMenu()

		if not callback:
			def _callback(info):
				i = info['index']
				if i < 0 or i >= len(items):
					return
				item = items[i]
				if not item or item.disabled or not item.callback:
					return
				item.callback()
			callback = _callback

		if self.applyPosition:
			self.applyPosition(popmenu)

		popmenu.Open(
			items=[item.text for item in items],
			highlightedItems=[
				item.text for item in items if item.highlighted],
			disabledItems=[
				item.text for item in items if item.disabled],
			dividersAfterItems=[
				item.text for item in items if item.dividerafter],
			checkedItems={
				item.text: item.checked
				for item in items
				if item.checked is not None
			},
			subMenuItems=[
				item.text for item in items if item.hassubmenu],
			callback=callback,
			callbackDetails=callbackDetails,
			autoClose=autoClose,
			rolloverCallback=rolloverCallback,
			allowStickySubMenus=allowStickySubMenus)

def _getPopMenu():
	popmenu = op.TDResources.op('popMenu')  # type: PopMenuExt
	return popmenu

class menus:

	@staticmethod
	def fromMouse(h='Left', v='Top', offset=(0, 0)):
		def _applyPosition(
				popmenu  # type: PopMenuExt
		):
			popmenu.SetPlacement(hAlign=h, vAlign=v, alignOffset=offset, matchWidth=False)
		return _MenuOpener(_applyPosition)

	@staticmethod
	def fromButton(buttonComp, h='Left', v='Bottom', matchWidth=False, offset=(0, 0)):
		if not buttonComp:
			return menus.fromMouse(h=h, v=v, offset=offset)

		def _applyPosition(
				popmenu  # type: PopMenuExt
		):
			popmenu.SetPlacement(
				buttonComp=buttonComp,
				hAttach=h, vAttach=v, matchWidth=matchWidth, alignOffset=offset)
		return _MenuOpener(_applyPosition)
