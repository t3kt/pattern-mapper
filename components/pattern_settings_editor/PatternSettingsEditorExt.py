import json

from common import ExtensionBase, loggedmethod
from typing import Any, Callable, Dict
import menu
from pattern_model import PatternData, PatternSettings, GroupInfo

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
			{'name': 'PatternData', 'dependable': False},
			{'name': 'PatternSettingsDict', 'dependable': 'deep'},
			{'name': 'Groups', 'dependable': 'deep'},
		]
		self.storage = StorageManager(
			self,
			self.ownerComp,
			storageSpecs,
		)
		# noinspection PyUnreachableCode
		if False:
			self.Steps = None  # type: DependList[DependList[int]]
			self.SelectedShapes = None  # type: DependList[int]
			self.PatternData = None  # type: PatternData
			self.PatternSettingsDict = None  # type: DependDict[str, Any]
			self.Groups = None  # type: DependList[DependDict[str, Any]]

		self.menuHandlers = {
			'Selection': {
				'Deselect All': lambda info: self._ClearSelection(),
				'Invert': lambda info: self._InvertSelection(),
				'Add All Steps': lambda info: self._AdjustSelection(adds=self._AllStepShapeIndices),
				'Remove All Steps': lambda info: self._AdjustSelection(removes=self._AllStepShapeIndices),
			},
			'Steps': {
				'Add': lambda info: self._SaveSelectionToNewStep(allowempty=True),
				'Delete': lambda info: self._DeleteStep(),
				'Clear': lambda info: self._ClearSteps(),
			}
		}  # type: Dict[str, Dict[str, Callable]]

	def LoadPatternData(self):
		jsondat = self.op('pattern_data_json')
		jsondat.par.loadonstartpulse.pulse()
		jsonstr = jsondat.text
		obj = json.loads(jsonstr) if jsonstr else {}
		patterndata = PatternData.FromJsonDict(obj)
		self.Groups = [
			self._CreateGroupDict(groupinfo)
			for groupinfo in patterndata.groups
		]

	@staticmethod
	def _CreateGroupDict(groupinfo: GroupInfo):
		return {
			'name': groupinfo.groupname,
			'generated': True,
			'info': groupinfo.ToJsonDict(),
			'shapes': groupinfo.allShapeIndices,
			'stepshapes': [
				list(step.shapeindices)
				for step in groupinfo.sequencesteps
			]
		}

	def _KeyState(self, name):
		return bool(self.op('key_states')[name])

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
					if self.statepar.Selectedstep == len(self.Steps):
						self._SaveSelectionToNewStep(allowempty=True)
					else:
						self.statepar.Selectedstep = len(self.Steps)
		else:
			if isshape:
				self._SaveSelectionToNewStep()
				self._AddToSelectedShapes(shapeindex)
			else:
				if self.statepar.Selectedstep == len(self.Steps):
					self._SaveSelectionToNewStep()
				else:
					self.statepar.Selectedstep = len(self.Steps)

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
		orig = list(self.SelectedShapes)
		inverted = [
			shape
			for shape in self._AllShapeIndices
			if shape not in orig
		]
		self.SelectedShapes = inverted

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

	def _DeleteStep(self, i=None):
		if i is None:
			i = int(self.statepar.Selectedstep)
		if i < 0 or i >= len(self.Steps):
			return
		shouldshift = self.statepar.Selectedstep >= i and i < len(self.Steps)
		del self.Steps[i]
		if shouldshift:
			self.statepar.Selectedstep += 1

	@property
	def HasSelectedStep(self):
		return 0 <= self.statepar.Selectedstep < len(self.Steps)

	@property
	def StepButtonLabels(self):
		labels = []
		for i, shapes in enumerate(self.Steps):
			labels.append(str(i) if shapes else '({})'.format(i))
		return labels + ['+']

	@property
	def _AllShapeIndices(self):
		return [int(v) for v in self.op('shape_attrs')['index'].vals]

	@property
	def _AllStepShapeIndices(self):
		shapes = []
		for step in self.Steps:
			for shape in step:
				if shape not in shapes:
					shapes.append(shape)
		return shapes

	def _GetStepShapes(self, i):
		if 0 <= i < len(self.Steps):
			return list(self.Steps[i])
		return []

	@loggedmethod
	def _AdjustSelection(self, adds=None, removes=None):
		shapes = list(self.SelectedShapes)
		if adds:
			for index in adds:
				if index not in shapes:
					shapes.append(index)
		if removes:
			for index in removes:
				if index in shapes:
					shapes.remove(index)
		self.SelectedShapes = shapes

	def OpenStepButtonContextMenu(self, button):
		i = button.digits
		if i is None:
			return
		menuitems = [
			menu.Item(
				'Delete',
				lambda: self._DeleteStep(i)
			),
			menu.Item(
				'Add To Selection',
				lambda: self._AdjustSelection(adds=self._GetStepShapes(i))
			),
			menu.Item(
				'Remove From Selection',
				lambda: self._AdjustSelection(removes=self._GetStepShapes(i))
			),
		]
		menu.fromButton(button).Show(menuitems, autoClose=True)

	def _GetGroupShapes(self, i):
		if 0 <= i < len(self.Groups):
			group = self.Groups[i]
			return list(group.get('shapes') or [])
		return []

	def _AddGroupToSelection(self, groupindex):
		pass

	@loggedmethod
	def OpenGroupContextMenu(self, button):
		i = int(
			button.par.Groupindex
			if hasattr(button.par, 'Groupindex') else
			button.parent.Group.par.Groupindex
		)
		menuitems = [
			menu.Item(
				'Add To Selection',
				lambda: self._AdjustSelection(adds=self._GetGroupShapes(i))
			),
			menu.Item(
				'Remove From Selection',
				lambda: self._AdjustSelection(removes=self._GetGroupShapes(i))
			),
		]
		menu.fromButton(button).Show(menuitems, autoClose=True)
