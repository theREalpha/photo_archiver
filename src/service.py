## Library imports
import os
import threading
import pickle
import webbrowser
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
from time import sleep

## Service Imports
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from src.logger import logger
from config import ENABLE_GALLERY
def flow_oa(CLIENT_SECRET_FILE,SCOPES, redirect_uri, port):
# Create authorization url using Google's oauth App Flow
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
	flow.redirect_uri=redirect_uri
	auth_url, _ =flow.authorization_url()

	# Custom Server to handle GET requests, store last_uri for creating cred tokens
	class CustomHandler(SimpleHTTPRequestHandler):
		def do_GET(self):
			if self.path=='/login':
				self.send_response(302)
				self.send_header('location',auth_url)
				self.end_headers()

			elif self.path.startswith("/login/auth"):
				self.send_response(200)
				self.send_header('Content-type','text/html')
				self.end_headers()
				self.server.last_uri= f"https://127.0.0.1:{port}"+self.path
				if ENABLE_GALLERY:
					htt= f"""<html>
		<head>
			<meta http-equiv="refresh" content="3;url=https://therealpha.ddns.net:{port-1}/gallery" />
		</head>
		<body>
			<h1>Redirecting in 3 seconds...</h1>
		</body>
	</html>"""
					## port-1 is the Landing Page port
				else: htt=f"""<html><body>return to terminal</body></html>"""
				self.wfile.write(htt.encode())
			elif self.path.endswith(".ico"):
				self.send_response(200)
				self.end_headers()
				self.wfile.write(b" ")
			else:
				self.send_response(301)
				self.send_header('location', f'https://therealpha.ddns.net:{port-1}')
				self.end_headers()

	class CustomHTTPServer(HTTPServer):
		last_uri= None

	# HTTPS server using self-signed certs running on a seperate thread
	server =CustomHTTPServer(('0.0.0.0', port), CustomHandler)
	ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	ctx.load_cert_chain(keyfile='web/certs/key.pem', certfile="web/certs/cert.pem")
	server.socket = ctx.wrap_socket(server.socket,server_side=True)
	# server.socket = ssl.wrap_socket(server.socket, keyfile='web/certs/key.pem', certfile="web/certs/cert.pem", server_side=True)
	server_thread= threading.Thread(target=server.serve_forever)
	try:
		server_thread.start()
	except Exception as e:
		logger.error(f"Failed to start server thread due to an exception")
		logger.error(f"{e.with_traceback()}")
		return None
	# webbrowser.open(f"https://127.0.0.1:{port}/login", 1, True)
	# Polls every 3s to check if last_uri is set and then shutdowns the server and thread
	while True:
		sleep(3)
		if server.last_uri:
			try:
				server.shutdown()
				server_thread.join()
			except Exception as e:
				logger.error("Exception encountered while trying to close server")
				logger.error(f"{e.with_traceback()}")
			break

	flow.fetch_token(authorization_response=server.last_uri)
	return flow

def create_creds(CLIENT_SECRET_FILE, SCOPES, over_air= True):
	port=62512
	if over_air:
		host="therealpha.ddns.net"
		redirect_uri=f"https://{host}:{port}/login/auth/"
		flow= flow_oa(CLIENT_SECRET_FILE, SCOPES, redirect_uri,port)
		return flow.credentials
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
	flow.run_local_server(port=port)
	return flow.credentials

def Create_Service(client_secret_file, api_name, api_version, over_air=True, *scopes):
	print(client_secret_file, api_name, api_version, scopes, sep='-')
	CLIENT_SECRET_FILE = client_secret_file
	API_SERVICE_NAME = api_name
	API_VERSION = api_version
	SCOPES = [scope for scope in scopes[0]]

	cred = None

	pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'

	if os.path.exists(pickle_file):
		with open(pickle_file, 'rb') as token:
			cred = pickle.load(token)
	if not cred or not cred.valid:
		if cred and cred.expired and cred.refresh_token:
			cred.refresh(Request())
		else:
			logger.info("Create new creds")
			cred=create_creds(CLIENT_SECRET_FILE,SCOPES, over_air)
		with open(pickle_file, 'wb') as token:
			pickle.dump(cred, token)

	try:
		service = build(API_SERVICE_NAME, API_VERSION, credentials=cred, static_discovery=False)
		logger.info(f"{API_SERVICE_NAME} service created successfully")
		return service
	except Exception as e:
		logger.error(f"Exception occured while trying to build service")
		logger.error(e.with_traceback())
		return None