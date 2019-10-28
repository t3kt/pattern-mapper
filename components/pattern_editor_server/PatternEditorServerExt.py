import json
from typing import Dict, Callable, Union
import urllib.parse

from common import ExtensionBase, loggedmethod, BaseDataObject, BaseDataObject2
from pattern_model import PatternData, PatternSettings

# noinspection PyUnreachableCode
if False:
	from _stubs import *

class _Request:
	def __init__(self, d: dict):
		self.d = d

	@property
	def method(self): return self.d.get('method')

	@property
	def uri(self): return self.d.get('uri')

	@property
	def clientAddress(self): return self.d.get('clientAddress')

	@property
	def serverAddress(self): return self.d.get('serverAddress')

class _Response:
	def __init__(self, d: dict):
		self.d = d

	@property
	def statusCode(self): return self.d.get('statusCode')

	@statusCode.setter
	def statusCode(self, val): self.d['statusCode'] = val

	@property
	def statusReason(self): return self.d.get('statusReason')

	@statusReason.setter
	def statusReason(self, val): self.d['statusReason'] = val

	@property
	def data(self): return self.d.get('data')

	@data.setter
	def data(self, val): self.d['data'] = val

class _Handler:
	def __call__(self, request: _Request, response: _Response):
		data = self._GetData(request.uri)
		response.data = data

	def _GetData(self, uri: str): raise NotImplementedError()

class _TextHandler(_Handler):
	def __init__(self, getter: Callable[[str], str]):
		self.getter = getter

	def _GetData(self, uri: str): return self.getter(uri)

class _JsonHandler(_Handler):
	def __init__(self, getter: Callable[[str], Union[BaseDataObject, BaseDataObject2]]):
		self.getter = getter

	def _GetData(self, uri):
		data = self.getter(uri)
		obj = data.ToJsonDict() if data else None
		return json.dumps(obj)

class PatternEditorServer(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)
		self.patterndata = None  # type: PatternData
		self.patternsettings = None  # type: PatternSettings
		self.handlers = {}  # type: Dict[str, _Handler]
		self._InitHandlers()

	def _InitHandlers(self):
		self.handlers = {
			'/patterndata.json': _JsonHandler(lambda uri: self._GetPatternData()),
			'/patternsettings.json': _JsonHandler(lambda uri: self._GetPatternSettings()),
			'/pattern.svg': _TextHandler(lambda uri: self._GetPatternSvg()),
		}

	def LoadPatternData(self):
		obj = self._GetObjFromDAT('pattern_data_json')
		self.patterndata = PatternData.FromJsonDict(obj)

	def LoadPatternSettings(self):
		obj = self._GetObjFromDAT('pattern_settings_json')
		self.patternsettings = PatternSettings.FromJsonDict(obj)

	def _GetObjFromDAT(self, path):
		jsondat = self.op(path)
		jsondat.par.loadonstartpulse.pulse()
		jsonstr = jsondat.text
		return json.loads(jsonstr) if jsonstr else {}

	def _z_UpdatePatternDefinitionFromJson(self, data: str):
		obj = json.loads(data)
		self.patterndata = PatternData.FromJsonDict(obj)

	def _GetPatternData(self):
		if not self.patterndata:
			self.LoadPatternData()
		return self.patterndata

	def _GetPatternSettings(self):
		if not self.patternsettings:
			self.LoadPatternSettings()
		return self.patternsettings

	def _GetPatternSvg(self):
		textdat = self.op('pattern_svg_xml')
		textdat.par.loadonstartpulse.pulse()
		return textdat.text

	@loggedmethod
	def OnHttpRequest(self, serverdat, requestobj, responseobj):
		request = _Request(requestobj)
		url = urllib.parse.urlparse(request.uri)
		self._LogEvent('URL: {}'.format(url))

		response = _Response(responseobj)
		response.statusCode = 200
		response.statusReason = 'OK'
		handler = self.handlers.get(request.uri)
		if handler:
			handler(request, response)
		else:
			response.data = '<b>Pattern Mapper: </b>' + serverdat.name
		return response.d

	def OnWebSocketOpen(self, serverdat, client):
		pass

	@staticmethod
	def OnWebSocketReceiveText(serverdat, client, data):
		serverdat.webSocketSendText(client, data)

	@staticmethod
	def OnWebSocketReceiveBinary(serverdat, client, data):
		serverdat.webSocketSendBinary(client, data)

	def OnServerStart(self, serverdat):
		pass

	def OnServerStop(self, serverdat):
		pass

