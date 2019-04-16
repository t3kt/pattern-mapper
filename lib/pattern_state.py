print('pattern_state.py loading...')

from collections import defaultdict
import json
import xml.etree.ElementTree as ET
from typing import Any, DefaultDict, Dict, List, Set, Tuple

if False:
	from ._stubs import *

try:
	from common import ExtensionBase
except ImportError:
	from .common import ExtensionBase

try:
	from common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod
except ImportError:
	from .common import simpleloggedmethod, hextorgb, keydefaultdict, loggedmethod
try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject

from pattern_model import BoolOpNames, GroupInfo, GroupSpec, SequenceStep, ShapeInfo


class ShapeSettingsEditor(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.par = ownerComp.par

	def GetState(self):
		return cleandict(mergedicts(
			self.par.Includepathoncolor and self._parValsDict('Pathoncolor[rgba]'),
			self.par.Includepathoffcolor and self._parValsDict('Pathoffcolor[rgba]'),
			self.par.Includepanelcolor and self._parValsDict('Panel*color[rgba]'),
			self.par.Includelocalscale and self._parValsDict('Localscale[xyz]'),
			self.par.Includelocalrotate and self._parValsDict('Localrotate[xyz]'),
			self.par.Includelocaltranslate and self._parValsDict('Localtranslate[xyz]'),
			self.par.Includepathphase and self._parValsDict('Pathphase'),
			self.par.Includepathperiod and self._parValsDict('Pathperiod', 'Pathreverse'),
		))

	def SetState(self, obj: Dict[str, Any], clearmissing=True):
		for switchpar, parnames in [
			(self.par.Includepathoncolor, ['Pathoncolor[rgba]']),
			(self.par.Includepathoffcolor, ['Pathoffcolor[rgba]']),
			(self.par.Includepanelcolor, ['Panel*color[rgba]']),
			(self.par.Includelocalscale, ['Localscale[xyz]']),
			(self.par.Includelocalrotate, ['Localrotate[xyz]']),
			(self.par.Includelocaltranslate, ['Localtranslate[xyz]']),
			(self.par.Includepathphase, ['Pathphase']),
			(self.par.Includepathperiod, ['Pathperiod', 'Pathreverse']),
		]:
			self._applyParVals(switchpar, parnames, obj=obj, clearmissing=clearmissing)

	def _parValsDict(self, *parnames):
		return {p.name: p.eval() for p in self.ownerComp.pars(*parnames)}

	def _applyParVals(self, switchpar, parnames, obj: Dict[str, Any], clearmissing: bool):
		pars = {p.name: p for p in self.ownerComp.pars(*parnames)}
		matchedany = False
		for p in pars:
			if p.name in obj:
				p.val = obj[p.name]
				matchedany = True
		if matchedany:
			switchpar.val = True
		elif clearmissing:
			switchpar.val = False
