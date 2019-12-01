from common import ExtensionBase
from pathlib import Path

# noinspection PyUnreachableCode
if False:
	from _stubs import *

class PatternStateGenManager(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)

	@property
	def _StateGen(self): return self.ownerComp.op('state_gen')

	@property
	def _StateGenTemplate(self): return self.ownerComp.op('state_gen_template')

	def OnToxFileChanged(self, toxFile):
		toxPath = Path(tdu.expandPath(toxFile))
		if toxPath.exists():
			self._LoadTox(toxFile)
		else:
			self._InitNew(toxFile)

	def _LoadTox(self, toxFile):
		gen = self._StateGen
		for child in gen.ops('*'):
			child.destroy()
		gen.par.externaltox = toxFile
		gen.par.reinitnet.pulse()

	def _InitNew(self, toxFile):
		gen = self._StateGen
		template = self._StateGenTemplate
		gen.par.externaltox = toxFile
		for child in gen.ops('*'):
			child.destroy()
		gen.copyOPs(template.ops('*'))

	def SaveTox(self):
		gen = self._StateGen
		toxFile = gen.par.externaltox.eval()
		gen.save(toxFile)

	def ShowInEditor(self, useActive=False):
		gen = self._StateGen
		if not gen:
			return
		pane = None
		if useActive:
			pane = _GetActiveEditor()
		if not pane:
			pane = _GetPaneByName('stategeneditor')
		if not pane:
			pane = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name='stategeneditor')
		pane.owner = gen

def _GetActiveEditor():
	pane = ui.panes.current
	if pane.type == PaneType.NETWORKEDITOR:
		return pane
	for pane in ui.panes:
		if pane.type == PaneType.NETWORKEDITOR:
			return pane

def _GetPaneByName(name):
	for pane in ui.panes:
		if pane.name == name:
			return pane
