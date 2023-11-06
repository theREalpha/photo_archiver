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

def create_creds(CLIENT_SECRET_FILE, SCOPES):
	host="therealpha.ddns.net"
	port=62511
	redirect_uri=f"https://{host}:{port}/"

	# Create authorization url using Google's oauth App Flow
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
	flow.redirect_uri=redirect_uri
	auth_url, _ =flow.authorization_url()

	# Custom Server to handle GET requests, store last_uri for creating cred tokens
	class CustomHandler(SimpleHTTPRequestHandler):
		def do_GET(self):
			global LAST_URI
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()

			if self.path=='/':
				self.wfile.write(f"""<html>
					 <body> Click <a href={auth_url}>here</a> to login into the account and start the process</body>
					   </html>""".encode())

			elif self.path.startswith("/?state="):
				self.server.last_uri= f"https://127.0.0.1:{port}"+self.path
				self.wfile.write(f"You can close this window".encode())

			else:
				pass

	class CustomHTTPServer(HTTPServer):
		last_uri= None

	# HTTPS server using self-signed certs running on a seperate thread
	server =CustomHTTPServer(('0.0.0.0', port), CustomHandler)
	server.socket = ssl.wrap_socket(server.socket, keyfile='certs/key.pem', certfile="certs/cert.pem", server_side=True)
	server_thread= threading.Thread(target=server.serve_forever)
	try:
		server_thread.start()
	except Exception as e:
		logger.error(f"Failed to start server thread due to an exception")
		logger.error(f"{e.with_traceback()}")
		return None
	webbrowser.open(f"https://127.0.0.1:{port}", 1, True)
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
	return flow.credentials

def Create_Service(client_secret_file, api_name, api_version, *scopes):
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
			cred=create_creds(CLIENT_SECRET_FILE,SCOPES)
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