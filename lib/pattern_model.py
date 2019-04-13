print('pattern_model.py loading...')

from typing import List

if False:
	from common.lib._stubs import *

try:
	from common import cleandict, mergedicts, BaseDataObject
except ImportError:
	from .common import cleandict, mergedicts, BaseDataObject

class ShapeInfo(BaseDataObject):
	def __init__(
			self,
			shapeindex: int,
			shapename: str,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'shapeindex': self.shapeindex,
			'shapename': self.shapename,
		}))

class SequenceStep(BaseDataObject):
	def __init__(
			self,
			sequenceindex=0,
			shapeindices: List[int]=None,
			isdefault=False,
			**attrs):
		super().__init__(**attrs)
		self.sequenceindex = sequenceindex
		self.shapeindices = list(shapeindices or [])
		self.isdefault = isdefault

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'sequenceindex': self.sequenceindex,
			'shapeindices': self.shapeindices,
			'isdefault': self.isdefault,
		}))

class GroupInfo(BaseDataObject):
	def __init__(
			self,
			groupname,
			groupindex=None,
			shapeindices: List[int]=None,
			sequencesteps: List[SequenceStep]=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.groupindex = groupindex
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'groupindex': self.groupindex,
			'shapeindices': self.shapeindices,
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
		}))
