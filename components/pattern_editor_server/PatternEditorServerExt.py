import json
from typing import Dict, Callable, Union

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

	@property
	def contentType(self): return self.d.get('Content-Type')

	@contentType.setter
	def contentType(self, val): self.d['Content-Type'] = val

class _Handler:
	def __init__(self, contentType: str = None, responseattrs: dict = None):
		self.contentType = contentType
		self.responseattrs = responseattrs or {}

	def Handle(self, request: _Request, response: _Response):
		data = self._GetData(request.uri)
		response.data = data
		response.d.update(self.responseattrs)
		if self.contentType:
			response.contentType = self.contentType

	def _GetData(self, uri: str): raise NotImplementedError()

class _TextHandler(_Handler):
	def __init__(self, getter: Callable[[str], str], contentType: str = None):
		super().__init__(contentType or 'text/plain')
		self.getter = getter

	def _GetData(self, uri: str): return self.getter(uri)

class _JsonHandler(_Handler):
	def __init__(self, getter: Callable[[str], Union[BaseDataObject, BaseDataObject2]]):
		super().__init__('application/json')
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
			'/pattern.svg': _TextHandler(lambda uri: self._GetPatternSvg(), 'image/svg+xml'),
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
		response = _Response(responseobj)
		response.statusCode = 200
		response.statusReason = 'OK'
		handler = self.handlers.get(request.uri)
		if handler:
			handler.Handle(request, response)
		else:
			response.data = '''
				<b>Pattern Mapper: </b>
				<hr/>
				<img src="pattern.svg" style="max-width: 80%;"/>
			'''
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

