import inspect
from typing import Union, Dict, TypeVar, Callable, List

_JsonValue = Union[str, float, int, bool, None, Dict[str, '_JsonValue'], List['_JsonValue']]
_ValT = TypeVar('_ValT')


def _identity(o): return o

def _optionalKwArgs(func: Callable):
	argnames = inspect.getfullargspec(func).args
	def _wrapper(*args, **kwargs):
		return func(
			*args,
			**{
				k: v
				for k, v in kwargs.items()
				if k in argnames
			}
		)
	return _wrapper


class JsonOpts:
	def __init__(
			self,
			condense=False,
			prefix='',
			capitalize=False,
			padtuples=False):
		self.condense = condense
		self.prefix = prefix
		self.capitalize = capitalize
		self.padtuples = padtuples

class TypeHandler:
	_registered = []  # type: List[TypeHandler]
	_registeredByType = {}

	def __init__(
			self,
			t: type,
			name: str=None):
		self.type = t
		self.name = name or t.__name__
		self.listHandler = None  # type: ListTypeHandler
		self.elementHandler = None  # type: TypeHandler

	def fromJsonValue(self, val: _JsonValue, opts: JsonOpts=None) -> _ValT:
		return self.type(val)

	def toJsonValue(self, obj: _ValT, opts: JsonOpts=None) -> _JsonValue:
		return obj

	def toJsonString(self, obj: _ValT) -> str:
		return str(obj)

class _CustomTypeHandler(TypeHandler):
	def __init__(
			self,
			t: type,
			name: str=None,
			fromJson: Callable[[_JsonValue], _ValT] = _identity,
			toJson: Callable[[_ValT], _JsonValue] = _identity,
			toJsonStr: Callable[[_ValT], str]=str):
		super().__init__(t, name)
		self._fromJson = _optionalKwArgs(fromJson)
		self._toJson = _optionalKwArgs(toJson)
		self._toJsonStr = toJsonStr

	def fromJsonValue(self, val: _JsonValue, opts: JsonOpts=None) -> _ValT:
		return self._fromJson(val)

	def toJsonValue(self, obj: _ValT, opts: JsonOpts=None) -> _JsonValue:
		return self._toJson(obj)

	def toJsonString(self, obj: _ValT):
		return self._toJsonStr(obj)


class ListTypeHandler(TypeHandler):
	def __init__(self, handler: TypeHandler):
		super().__init__(handler.type, name='List({})'.format(handler.name))
		self.elementHandler = handler

	def fromJsonValue(self, val: _JsonValue, opts: JsonOpts=None):
		if isinstance(val, str) and opts and opts.condense:
			raise NotImplementedError()
		return [
			self.elementHandler.fromJsonValue(v, opts=opts)
			for v in (val or [])
		]

	def toJsonValue(self, obj: _ValT, opts: JsonOpts=None):
		if opts.condense:
			raise NotImplementedError()
		return [
			self.elementHandler.toJsonValue(o, opts=opts)
			for o in (obj or [])
		]

class TupleTypeHandler(ListTypeHandler):
	def __init__(self, handler: TypeHandler, length: int, *defaults: _ValT):
		super().__init__(handler)
		self.length = length
		self.defaults = defaults

	def _adjustList(self, vals: List):
		vals = vals or []
		n = len(vals)
		if n == self.length:
			return vals
		elif n > self.length:
			return vals[:n]
		else:  # n < self.length
			padded = []
			for i in range(n):
				if i < n:
					padded.append(vals[i])
				elif i < len(self.defaults):
					padded.append(self.defaults[i])
				else:
					padded.append(self.defaults[-1])
			return padded

	def fromJsonValue(self, val: _JsonValue, opts: JsonOpts=None):
		return self._adjustList(super().fromJsonValue(val, opts=opts))

	def toJsonValue(self, obj: _ValT, opts: JsonOpts=None):
		vals = super().toJsonValue(obj, opts=opts)
		return self._adjustList(vals) if opts and opts.padtuples else vals

class _Registry:
	def __init__(self):
		self._handlers = []  # type: List[TypeHandler]
		self._handlersbytype = {}  # type: Dict[type, TypeHandler]
		self._listhandlersbytype = {}  # type: Dict[type, TypeHandler]

	def add(self, handler: Union[TypeHandler, type], withlist=False):
		if isinstance(handler, type):
			handler = TypeHandler(type),
		self._handlers.append(handler)
		if isinstance(handler, ListTypeHandler):
			if withlist:
				raise Exception('cannot provide withlist for a handler that is already a list handler')
			self._listhandlersbytype[handler.type] = handler
		else:
			self._handlersbytype[handler.type] = handler
			if withlist:
				handler.listHandler = ListTypeHandler(handler)
				self.add(handler.listHandler)
		return handler

	def addAll(self, *handlers: 'TypeHandler'): return [self.add(handler) for handler in handlers]

	def of(self, t: type): return self._handlersbytype[t]

	def listOf(self, t: type): return self._listhandlersbytype[t]

Registry = _Registry()
strHandler = Registry.add(str, withlist=True)
boolHandler = Registry.add(bool, withlist=True)
floatHandler = Registry.add(float, withlist=True)
intHandler = Registry.add(
	_CustomTypeHandler(
		int,
		fromJson=lambda v: v if isinstance(v, int) else int(float(v)),
	),
	withlist=True)



class AttrSchema:
	def __init__(
			self,
			name: str,
			t: type,
			jsonname: str = None,
			default: _ValT = None,
			page: str = None):
		self.name = name
		self.type = t
		self.jsonname = jsonname or name.lower()
		self.default = default
		self.page = page


class ObjectSchema(TypeHandler):
	def __init__(
			self,
			t: type,
			*attrs: AttrSchema,
			defaultpage: str = 'Custom'):
		super().__init__(t)
		self.attrs = list(attrs or [])
		self.attrsbyname = {attr.name: attr for attr in self.attrs}
		self.defaultpage = defaultpage

	def toJsonString(self, obj: _ValT):
		raise Exception('{} does not support toJsonString()'.format(type(self)))

	def toJsonValue(self, obj: _ValT, opts: JsonOpts=None):
		raise NotImplementedError()

	def fromJsonValue(self, val: _JsonValue, opts: JsonOpts=None):
		raise NotImplementedError()
