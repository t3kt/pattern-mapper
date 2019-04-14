print('pattern_model.py loading...')

from colorsys import rgb_to_hsv
from typing import Any, List, Tuple

if False:
	from ._stubs import *

try:
	from common import cleandict, mergedicts, BaseDataObject
except ImportError:
	from .common import cleandict, mergedicts, BaseDataObject

class ShapeInfo(BaseDataObject):
	def __init__(
			self,
			shapeindex: int,
			shapename: str,
			parentpath: str,
			color: Tuple,
			**attrs):
		super().__init__(**attrs)
		self.shapeindex = shapeindex
		self.shapename = shapename
		self.parentpath = parentpath
		self.color = color

	@property
	def hsvcolor(self):
		if not self.color:
			return None
		return rgb_to_hsv(self.color[0], self.color[1], self.color[2])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'shapeindex': self.shapeindex,
			'shapename': self.shapename,
			'parentpath': self.parentpath,
			'color': self.color,
		}))

class SequenceStep(BaseDataObject):
	def __init__(
			self,
			sequenceindex=0,
			shapeindices: List[int]=None,
			isdefault: bool=None,
			inferredfromvalue: Any=None,
			**attrs):
		super().__init__(**attrs)
		self.sequenceindex = sequenceindex
		self.shapeindices = list(shapeindices or [])
		self.isdefault = isdefault
		self.inferredfromvalue = inferredfromvalue

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'sequenceindex': self.sequenceindex,
			'shapeindices': self.shapeindices,
			'isdefault': self.isdefault,
			'inferredfromvalue': self.inferredfromvalue,
		}))

class GroupInfo(BaseDataObject):
	def __init__(
			self,
			groupname,
			grouppath=None,
			inferencetype: str=None,
			inferredfromvalue: Any=None,
			shapeindices: List[int]=None,
			sequencesteps: List[SequenceStep]=None,
			**attrs):
		super().__init__(**attrs)
		self.groupname = groupname
		self.grouppath = grouppath
		self.inferencetype = inferencetype
		self.inferredfromvalue = inferredfromvalue
		self.shapeindices = list(shapeindices or [])
		self.sequencesteps = list(sequencesteps or [])

	def ToJsonDict(self):
		return cleandict(mergedicts(self.attrs, {
			'groupname': self.groupname,
			'grouppath': self.grouppath,
			'inferencetype': self.inferencetype,
			'inferredfromvalue': self.inferredfromvalue,
			'shapeindices': self.shapeindices,
			'sequencesteps': SequenceStep.ToJsonDicts(self.sequencesteps),
		}))
