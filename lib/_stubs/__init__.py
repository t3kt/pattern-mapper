# trick pycharm

# noinspection PyShadowingBuiltins
import typing as _T


class _Expando:
	def __init__(self):
		pass

mod = _Expando()
ui = _Expando()
ui.panes = []
ui.panes.current = None
ui.status = ''
PaneType = _Expando()
PaneType.NETWORKEDITOR = None
ext = _Expando()

class project:
	name = ''
	folder = ''

class _Parent:
	def __call__(self, *args, **kwargs) -> '_AnyOpT':
		pass

	def __getattr__(self, item):
		pass

class OP:
	id: int
	path: str
	name: str
	par: _T.Any
	customTuplets: _T.List[_T.Tuple['Par']]
	parent: '_Parent'
	storage: _T.Dict[str, _T.Any]
	isBase: bool
	isCOMP: bool
	isTOP: bool
	isCHOP: bool
	isDAT: bool
	isObject: bool
	isPanel: bool
	isSOP: bool
	depth: int
	tags: _T.Set[str]
	valid: bool
	icon: str

	def __init__(self): pass

	def destroy(self): pass

	def op(self, path) -> '_AnyOpT': pass
	def ops(self, *args) -> _T.List['_AnyOpT']: pass
	def findChildren(self, maxDepth=1, tags=None) -> '_T.List[_AnyOpT]': pass
	def copy(self, o: '_AnyOpT', name=None) -> 'op': pass
	def create(self, OPtype, name, initialize=True) -> '_AnyOpT': pass
	def shortcutPath(self, o: '_AnyOpT', toParName=None) -> str: pass
	def relativePath(self, o: '_AnyOpT') -> str: pass
	def openMenu(self, x=None, y=None): pass
	def var(self, name, search=True) -> str: pass
	def evalExpression(self, expr) -> _T.Any: pass
	def dependenciesTo(self, o: '_AnyOpT') -> _T.List['_AnyOpT']: pass
	def changeType(self, optype: type) -> '_AnyOpT': pass
	def copyParameters(self, o: '_AnyOpT', custom=True, builtin=True): pass
	def cook(self, force=False, recurse=False): pass
	def pars(self, pattern) -> _T.List['Par']: pass

	def openParameters(self): pass
	def openViewer(self, unique=False, borders=True): pass
	def closeViewer(self): pass

	def store(self, key, value): pass
	def unstore(self, keys1, *morekeys): pass
	def storeStartupValue(self, key, value): pass
	def unstoreStartupValue(self, *keys): pass
	def fetch(self, key, default, search=True, storeDefault=False): pass
	def fetchOwner(self, key) -> '_AnyOpT': pass

	def addScriptErrors(self, msg): pass
	def addError(self, msg): pass
	def addWarning(self, msg): pass
	def errors(self, recurse=False) -> str: pass
	def warnings(self, recurse=False) -> str: pass
	def scriptErrors(self, recurse=False) -> str: pass
	def clearScriptErrors(self, recurse=False, error='*'): pass

	TDResources = _Expando()

def op(path) -> '_AnyOpT': pass

op.TDResources = _Expando()
op.TDResources.op = op

def ops(*paths) -> _T.List['_AnyOpT']: pass

def var(name) -> str: pass

class _TD_ERROR(Exception):
	pass

class td:
	error = _TD_ERROR

	@staticmethod
	def run(codeorwhatever, delayFrames=0, delayMilliSeconds=0, delayRef=None): pass

	class Attribute:
		def __init__(self):
			self.owner = None  # type: OP
			self.name = ''
			self.size = 0
			self.type = None  # type: type
			self.default = None  # type: _T.Union[float, int, str, tuple, _Position, _Vector]

del _TD_ERROR


class _Matrix:
	vals: _T.List[float]
	rows: _T.List[_T.List[float]]
	cols: _T.List[_T.List[float]]

	def __init__(self, *values): pass

	def transpose(self): pass
	def invert(self): pass
	def determinant(self) -> float: pass
	def copy(self) -> '_Matrix': pass
	def identity(self): pass
	def translate(self, tx, ty, tz, fromRight=False): pass
	def rotate(self, rx, ry, rz, fromRight=False, pivot=None): pass
	def rotateOnAxis(self, rotationAxis, angle, fromRight=False, pivot=None): pass
	def scale(self, sx, sy, sz, fromRight=False, pivot=None): pass
	def lookat(self, eyePos, target, up): pass
	def decompose(self) -> _T.Tuple[_T.Tuple]: pass

class _Position:
	x: int
	y: int
	z: int

	def __init__(self, *vals): pass

	def translate(self, x, y, z): pass

	def scale(self, x, y, z): pass

	def copy(self) -> '_Position': pass

	def __getitem__(self, item: int) -> float: pass
	def __setitem__(self, key, value): pass
	def __mul__(self, other: _T.Union[float, _Matrix]) -> _T.Union[float, '_Position']: pass
	def __add__(self, other: _T.Union[float, '_Position', '_Vector']) -> _T.Union[float, '_Position']: pass
	def __sub__(self, other: _T.Union[float, '_Position', '_Vector']) -> _T.Union[float, '_Position']: pass
	def __div__(self, other: float) -> '_Position': pass
	def __abs__(self) -> '_Position': pass
	def __neg__(self) -> '_Position': pass


class _Vector:
	x: int
	y: int
	z: int

	def __init__(self, *vals): pass

	def translate(self, x, y, z): pass
	def scale(self, x, y, z): pass
	def __getitem__(self, item: int) -> float: pass
	def __setitem__(self, key, value): pass
	def normalize(self): pass
	def length(self) -> float: pass
	def lengthSquared(self) -> float: pass
	def copy(self) -> '_Vector': pass
	def distance(self, vec: '_Vector') -> float: pass
	def lerp(self, vec: '_Vector', t: float) -> '_Vector': pass
	def slerp(self, vec: '_Vector', t: float) -> '_Vector': pass
	def project(self, vec1: '_Vector', vec2: '_Vector'): pass
	def reflect(self, vec: '_Vector'): pass

class _ArcBall:
	def beginPan(self, u, v) -> None: pass
	def beginRotate(self, u, v) -> None: pass
	def beginDolly(self, u, v) -> None: pass
	def pan(self, u, v) -> None: pass
	def panTo(self, u, v, scale=1.0) -> None: pass
	def rotateTo(self, u, v, scale=1.0) -> None: pass
	def dolly(self, z) -> None: pass
	def dollyTo(self, u, v, scale=1.0) -> None: pass
	def transform(self) -> _Matrix: pass
	def setTransform(self, matrix: _Matrix) -> None: pass
	def identity(self) -> None: pass

class tdu:
	@staticmethod
	def legalName(s):
		return s

	# noinspection PyShadowingBuiltins
	@staticmethod
	def clamp(inputVal, min, max): pass

	@staticmethod
	def remap(inputVal, fromMin, fromMax, toMin, toMax): pass

	class Dependency:
		def __init__(self, _=None):
			self.val = None

		def modified(self): pass

	Position = _Position
	Vector = _Vector
	Matrix = _Matrix

	# noinspection PyShadowingBuiltins
	@staticmethod
	def split(string, eval=False)-> _T.List[str]: pass

	@staticmethod
	def match(pattern, inputList, caseSensitive=True) -> _T.List[str]: pass

	ArcBall = _ArcBall

JustifyType = _Expando()
JustifyType.TOPLEFT, JustifyType.TOPCENTER, JustifyType.TOPRIGHT, JustifyType.CENTERLEFT = 0, 0, 0, 0
JustifyType.CENTER = 0
JustifyType.CENTERRIGHT, JustifyType.BOTTOMLEFT, JustifyType.BOTTOMCENTER, JustifyType.BOTTOMRIGHT = 0, 0, 0, 0

ParMode = _Expando()
ParMode.CONSTANT = ParMode.EXPRESSION = ParMode.EXPORT = 0

ExpandoStub = _Expando

class Par:
	def eval(self): pass

class Cell:
	val: str
	row: int
	col: int

_NameOrIndex = _T.Union[str, int]

class DAT(OP):
	def row(self, nameorindex) -> _T.List[Cell]: pass
	def col(self, nameorindex) -> _T.List[Cell]: pass
	def clear(self): pass
	def appendRow(self, cells: _T.List[Cell]): pass
	def appendCol(self, cells: _T.List[Cell]): pass
	def appendRows(self, cells: _T.List[_T.List[Cell]]): pass
	def appendCols(self, cells: _T.List[_T.List[Cell]]): pass
	def __getitem__(self, row: _NameOrIndex, col: _NameOrIndex) -> Cell: pass
	def __setitem__(self, rowcol: _T.Tuple[_NameOrIndex, _NameOrIndex], value): pass

COMP = OP
CHOP = OP
SOP = OP
MAT = OP

_AnyOpT = _T.Union[OP, DAT, COMP, CHOP, SOP, MAT]

baseCOMP = panelCOMP = COMP
evaluateDAT = mergeDAT = nullDAT = parameterexecuteDAT = tableDAT = textDAT = scriptDAT = DAT
parameterCHOP = nullCHOP = selectCHOP = CHOP
scriptSOP = SOP

class app:
	name = ''

class RenderPickEvent(tuple):
	u: float
	v: float
	select: bool
	selectStart: bool
	selectEnd: bool
	pickOp: OP
	pos: _Position
	texture: _Position
	color: _T.Tuple[float, float, float, float]
	normal: _Vector
	depth: float
	instanceId: int

def debug(*args):
	pass

