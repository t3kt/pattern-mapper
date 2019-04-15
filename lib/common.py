from collections import defaultdict
import datetime
import json
from typing import Dict, Iterable, List, Optional, Union
import sys

print('common.py loading...')

if False:
	from common.lib._stubs import *


_TimestampFormat = '[%H:%M:%S]'
_PreciseTimestampFormat = '[%H:%M:%S.%f]'

def _LoggerTimestamp():
	return datetime.datetime.now().strftime(
		# _TimestampFormat
		_PreciseTimestampFormat
	)

def Log(msg, file=None):
	print(
		_LoggerTimestamp(),
		msg,
		file=file)
	file.flush()

class IndentedLogger:
	def __init__(self, outfile=None):
		self._indentLevel = 0
		self._indentStr = ''
		self._outFile = outfile

	def _AddIndent(self, amount):
		self._indentLevel += amount
		self._indentStr = '\t' * self._indentLevel

	def Indent(self):
		self._AddIndent(1)

	def Unindent(self):
		self._AddIndent(-1)

	def LogEvent(self, path, opid, event, indentafter=False, unindentbefore=False):
		if unindentbefore:
			self.Unindent()
		if event:
			if not path and not opid:
				Log('%s%s' % (self._indentStr, event), file=self._outFile)
			elif not opid:
				Log('%s%s %s' % (self._indentStr, path or '', event), file=self._outFile)
			else:
				Log('%s[%s] %s %s' % (self._indentStr, opid or '', path or '', event), file=self._outFile)
		if indentafter:
			self.Indent()

	def LogBegin(self, path, opid, event):
		self.LogEvent(path, opid, event, indentafter=True)

	def LogEnd(self, path, opid, event):
		self.LogEvent(path, opid, event, unindentbefore=True)

class _Tee:
	def __init__(self, *files):
		self.files = files

	def write(self, obj):
		for f in self.files:
			f.write(obj)
			# f.flush()  # make the output to be visible immediately

	def flush(self):
		for f in self.files:
			f.flush()

def _InitFileLog():
	f = open(project.name + '-log.txt', mode='a')
	print('\n-----[Initialize Log: {}]-----\n'.format(
		datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')), file=f)
	f.flush()
	return IndentedLogger(outfile=_Tee(sys.stdout, f))

#_logger = IndentedLogger()
_logger = _InitFileLog()

class LoggableBase:
	def _GetLogId(self) -> Optional[str]:
		return None

	def _LogEvent(self, event, indentafter=False, unindentbefore=False):
		raise NotImplementedError()

	def _LogBegin(self, event):
		self._LogEvent(event, indentafter=True)

	def _LogEnd(self, event=None):
		self._LogEvent(event, unindentbefore=True)

class ExtensionBase(LoggableBase):
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp  # type: op
		self.enablelogging = True
		self.par = ownerComp.par
		self.path = ownerComp.path
		self.op = ownerComp.op
		self.ops = ownerComp.ops
		# trick pycharm
		if False:
			self.storage = {}
			self.docked = []
			self.destroy = ownerComp.destroy

	def _GetLogId(self):
		if not self.ownerComp.valid or not hasattr(self.ownerComp.par, 'opshortcut'):
			return None
		return self.ownerComp.par.opshortcut.eval()

	def _LogEvent(self, event, indentafter=False, unindentbefore=False):
		if self.enablelogging:
			_logger.LogEvent(
				self.ownerComp.path,
				self._GetLogId(),
				event,
				indentafter=indentafter,
				unindentbefore=unindentbefore)

class LoggableSubComponent(LoggableBase):
	def __init__(self, hostobj: LoggableBase, logprefix: str=None):
		self.hostobj = hostobj
		self.logprefix = logprefix if logprefix is not None else type(self).__name__

	def _LogEvent(self, event, indentafter=False, unindentbefore=False):
		if self.hostobj is None:
			return
		if self.logprefix and event:
			event = self.logprefix + ' ' + event
		self.hostobj._LogEvent(event, indentafter=indentafter, unindentbefore=unindentbefore)

def _defaultformatargs(args, kwargs):
	if not args:
		return kwargs or ''
	if not kwargs:
		return args
	return '{} {}'.format(args, kwargs)

def _decoratewithlogging(func, formatargs):
	def wrapper(self: ExtensionBase, *args, **kwargs):
		self._LogBegin('{}({})'.format(func.__name__, formatargs(args, kwargs)))
		try:
			return func(self, *args, **kwargs)
		finally:
			self._LogEnd()
	return wrapper

def loggedmethod(func):
	return _decoratewithlogging(func, _defaultformatargs)

def simpleloggedmethod(func):
	return customloggedmethod(omitargs=True)(func)

def customloggedmethod(
		omitargs: Union[bool, List[str]]=None):
	if not omitargs:
		formatargs = _defaultformatargs
	elif omitargs is True:
		def formatargs(*_):
			return ''
	elif not isinstance(omitargs, (list, tuple, set)):
		raise Exception('Invalid "omitargs" specifier for loggedmethod: {!r}'.format(omitargs))
	else:
		def formatargs(args, kwargs):
			return _defaultformatargs(args, excludekeys(kwargs, omitargs))

	return lambda func: _decoratewithlogging(func, formatargs)

def cleandict(d):
	if not d:
		return None
	return {
		key: val
		for key, val in d.items()
		if not (val is None or (isinstance(val, (str, list, dict, tuple)) and len(val) == 0))
	}

def mergedicts(*parts):
	x = {}
	for part in parts:
		if part:
			x.update(part)
	return x

def excludekeys(d, keys):
	if not d:
		return {}
	return {
		key: val
		for key, val in d.items()
		if key not in keys
	}

class BaseDataObject:
	def __init__(self, **attrs):
		self.attrs = attrs

	def ToJsonDict(self) -> dict:
		raise NotImplementedError()

	def __repr__(self):
		return '{}({!r})'.format(self.__class__.__name__, self.ToJsonDict())

	@classmethod
	def FromJsonDict(cls, obj):
		return cls(**obj)

	@classmethod
	def FromJsonDicts(cls, objs: List[Dict]):
		return [cls.FromJsonDict(obj) for obj in objs] if objs else []

	@classmethod
	def FromOptionalJsonDict(cls, obj, default=None):
		return cls.FromJsonDict(obj) if obj else default

	@classmethod
	def FromJsonDictMap(cls, objs: Dict[str, Dict]):
		if not objs:
			return {}
		results = {}
		for key, obj in objs.items():
			val = cls.FromOptionalJsonDict(obj)
			if val:
				results[key] = val
		return results

	@classmethod
	def ToJsonDicts(cls, nodes: 'Iterable[BaseDataObject]'):
		return [n.ToJsonDict() for n in nodes] if nodes else []

	@classmethod
	def ToJsonDictMap(cls, nodes: 'Dict[str, BaseDataObject]'):
		return {
			path: node.ToJsonDict()
			for path, node in nodes.items()
		} if nodes else {}

	def WriteJsonTo(self, filepath):
		obj = self.ToJsonDict()
		with open(filepath, mode='w') as outfile:
			json.dump(obj, outfile, indent='  ')

	@classmethod
	def ReadJsonFrom(cls, filepath):
		with open(filepath, mode='r') as infile:
			obj = json.load(infile)
		return cls.FromJsonDict(obj)

	def AddToTable(self, dat, attrs=None):
		obj = self.ToJsonDict()
		attrs = mergedicts(obj, attrs)
		vals = []
		for col in dat.row(0):
			val = attrs.get(col.val, '')
			if isinstance(val, bool):
				val = 1 if val else 0
			elif isinstance(val, (list, set, tuple)):
				val = ' '.join(val)
			vals.append(val)
		dat.appendRow(vals)

	def UpdateInTable(self, rowid, dat, attrs=None):
		rowcells = dat.row(rowid)
		if not rowcells:
			self.AddToTable(dat, attrs)
		else:
			obj = self.ToJsonDict()
			attrs = mergedicts(obj, attrs)
			for cell in rowcells:
				col = dat[cell.row, 0]
				val = attrs.get(col.val, '')
				if isinstance(val, bool):
					val = 1 if val else 0
				elif isinstance(val, (list, set, tuple)):
					val = ' '.join(val)
				cell.val = val

def hextorgb(hexcolor: str):
	if not hexcolor:
		return None
	if hexcolor.startswith('#'):
		hexcolor = hexcolor[1:]
	return _HEXDEC[hexcolor[0:2]], _HEXDEC[hexcolor[2:4]], _HEXDEC[hexcolor[4:6]]

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}


# variant of defaultdict that passes the key to the factory function
# https://stackoverflow.com/questions/2912231/is-there-a-clever-way-to-pass-the-key-to-defaultdicts-default-factory
class keydefaultdict(defaultdict):
	def __missing__(self, key):
		if self.default_factory is None:
			raise KeyError(key)
		else:
			ret = self[key] = self.default_factory(key)
			return ret