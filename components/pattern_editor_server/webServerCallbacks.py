# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields. The dictionary will always contain the below entries, plus any additional entries dependent on the contents of the request
# 		'method' - The HTTP method of the request (ie. 'GET', 'PUT').
# 		'uri' - The client's requested URI.
# 		'clientAddress' - The client's address.
# 		'serverAddress' - The server's address.
# response - A dictionary defining the response, to be filled in during the request method. Additional fields not specified below can be added (eg. response['content-type'] = 'application/json').
# 		'statusCode' - A valid HTTP status code integer (ie. 200, 401, 404). Default is 404.
# 		'statusReason' - The reason for the above status code being returned (ie. 'Not Found.').
# 		'data' - The data to send back to the client. If displaying a web-page, any HTML would be put here.

# return the response dictionary
def onHTTPRequest(webServerDAT, request, response):
	return ext.Server.OnHttpRequest(webServerDAT, request, response)

def onWebSocketOpen(webServerDAT, client):
	ext.Server.OnHttpRequest(webServerDAT, client)

def onWebSocketReceiveText(webServerDAT, client, data):
	webServerDAT.webSocketSendText(client, data)

def onWebSocketReceiveBinary(webServerDAT, client, data):
	webServerDAT.webSocketSendBinary(client, data)

def onServerStart(webServerDAT):
	ext.Server.OnServerStart(webServerDAT)

def onServerStop(webServerDAT):
	ext.Server.OnServerStop(webServerDAT)
	