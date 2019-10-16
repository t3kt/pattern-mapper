import json
import pathlib
import urllib.parse

print('pattern_server.py loading...')

if False:
	from ._stubs import *

try:
	from common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod
except ImportError:
	from .common import cleandict, excludekeys, mergedicts, BaseDataObject, transformkeys, ExtensionBase, loggedmethod

from pattern_model import *
from pattern_loader import PatternBuilder, PatternLoader

class PatternServer(ExtensionBase):
	def __init__(self, ownerComp):
		super().__init__(ownerComp)

	@property
	def _PatternBuilder(self) -> PatternBuilder:
		return self.ownerComp.par.Patternbuilder.eval()
	@property
	def _PatternLoader(self) -> PatternLoader:
		return self.ownerComp.par.Patternloader.eval()

	@property
	def _PatternData(self) -> PatternData:
		raise NotImplementedError()

	@_PatternData.setter
	def _PatternData(self, newpatterndata: PatternData):
		self._whatever = newpatterndata
		raise NotImplementedError()

	def GetPatternDefinitionJson(self):
		obj = self._PatternData.ToJsonDict()
		return json.dumps(obj)

	def UpdatePatternDefinitionFromJson(self, data: str):
		obj = json.loads(data)
		self._PatternData = PatternData.FromJsonDict(obj)
		pass

	@loggedmethod
	def OnHttpRequest(self, serverdat, requestobj, responseobj):
		request = _Request(requestobj)
		url = urllib.parse.urlparse(request.uri)


		response = _Response(responseobj)
		response.statusCode = 200
		response.statusReason = 'OK'
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

	def _HandleStaticRequest(self, url: urllib.parse.ParseResult):
		staticdirpath = self.ownerComp.par.Staticdir.eval()
		if '..' in url.path:
			raise Exception('Unsupported path: {}'.format(url))
		pass


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

