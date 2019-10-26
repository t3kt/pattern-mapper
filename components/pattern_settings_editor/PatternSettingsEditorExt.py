from common import ExtensionBase, loggedmethod
from typing import Callable, Dict

try:
	from TDStoreTools import DependDict, DependList, StorageManager
except ImportError:
	from _stubs.TDStoreTools import DependDict, DependList, StorageManager

# noinspection PyUnreachableCode
if False:
	from _stubs import *

class PatternSettingsEditor(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.DBG_lastEvent = None
		self.statepar = ownerComp.op('state').par

		storageSpecs = [
			{'name': 'Steps', 'default': [], 'dependable': 'deep'},
			{'name': 'SelectedShapes', 'default': [], 'dependable': True},
			{'name': 'SelectedStep', 'default': None},
		]
		self.storage = StorageManager(
			self,
			self.ownerComp,
			storageSpecs,
		)
		# noinspection PyUnreachableCode
		if False:
			self.Steps = DependList()  # type: DependList[DependList[int]]
			self.SelectedShapes = DependList()  # type: DependList[int]

		self.menuHandlers = {
			'Selection': {
				'Deselect All': lambda info: self._ClearSelection(),
				'Invert': lambda info: self._InvertSelection(),
			},
			'Steps': {
				'Clear': lambda info: self._ClearSteps(),
				'Add': lambda info: self._SaveSelectionToNewStep(allowempty=True),
			}
		}  # type: Dict[str, Dict[str, Callable]]

	def _KeyState(self, name):
		return bool(self.op('key_states')[name])

	# @loggedmethod
	def OnRenderPickEvent(self, chop, event: 'RenderPickEvent'):
		self.DBG_lastEvent = event
		picked = bool(chop['picked'])
		trigger = bool(chop['trigger'])
		shapeindex = int(chop['shapeIndex'])
		alt = self._KeyState('alt')
		shift = self._KeyState('shift')
		ctrl = self._KeyState('ctrl')
		# self._LogEvent('picked: {} trigger: {} shapeIndex: {} keys: {} {} {}\n\t{}'.format(
		# 	picked, trigger, shapeindex,
		# 	'ALT' if alt else '',
		# 	'SHIFT' if shift else '',
		# 	'CTRL' if ctrl else '',
		# 	event,
		# ))

		if not picked or not trigger:
			return

		isshape = 'hidden_picker_panels_geo' in event.pickOp.path
		if alt:
			if not shift and not ctrl:
				if isshape:
					self._RemoveFromSelectedShapes(shapeindex)
				else:
					self._ClearSelection()
		elif ctrl:
			if not alt and not shift:
				if isshape:
					self._ToggleInShapeSelection(shapeindex)
		elif shift:
			if not alt and not ctrl:
				if isshape:
					self._AddToSelectedShapes(shapeindex)
				else:
					self._SaveSelectionToNewStep(allowempty=True)
		else:
			self._SaveSelectionToNewStep()
			if isshape:
				self._AddToSelectedShapes(shapeindex)

	@loggedmethod
	def _AddToSelectedShapes(self, shapeindex):
		if shapeindex not in self.SelectedShapes:
			self.SelectedShapes.append(shapeindex)

	@loggedmethod
	def _RemoveFromSelectedShapes(self, shapeindex):
		if not self.SelectedShapes or shapeindex not in self.SelectedShapes:
			return False
		self.SelectedShapes.remove(shapeindex)
		return True

	@loggedmethod
	def _ToggleInShapeSelection(self, shapeindex):
		if self._RemoveFromSelectedShapes(shapeindex):
			return
		self._AddToSelectedShapes(shapeindex)

	@loggedmethod
	def _SaveSelectionToNewStep(self, allowempty=False):
		if not allowempty and not self.SelectedShapes:
			return
		shapes = self.SelectedShapes.getRaw(None)
		self.Steps.append(shapes)
		self.SelectedShapes.clear()
		self.statepar.Selectedstep += 1

	@loggedmethod
	def _ClearSteps(self):
		self.Steps.clear()

	@loggedmethod
	def _ClearSelection(self):
		self.SelectedShapes.clear()

	@loggedmethod
	def _InvertSelection(self):
		pass

	def OnMenuAction(self, menuname: str, info: dict):
		action = info['item']
		if menuname in self.menuHandlers:
			handler = self.menuHandlers[menuname].get(action, None)
			if handler:
				handler(info)

	def _SelectShapesInStep(self, i):
		shapes = self.Steps[i] or []
		self.SelectedShapes = shapes

	def _SelectStep(self, i):
		stepcount = len(self.Steps)
		if i < 0:
			return
		if i >= stepcount:
			self._ClearSelection()
		else:
			self._SelectShapesInStep(i)

	def OnStateParChange(self, par):
		if par.name == 'Selectedstep':
			self._SelectStep(int(par))

	def OpenStepButtonContextMenu(self, button):
		pass
