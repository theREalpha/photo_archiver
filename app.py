import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import requests
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
def dup_pic(name):
	if os.path.isfile(name):
		i=1
		named=name[:-4]+"_"+str(i)+name[-4:]
		while os.path.isfile(named):
			i+=1
			named= name[:-4]+"_"+str(i)+name[-4:]
		return named
	return name
def Create_Service(client_secret_file, api_name, api_version, *scopes):
	print(client_secret_file, api_name, api_version, scopes, sep='-')
	CLIENT_SECRET_FILE = client_secret_file
	API_SERVICE_NAME = api_name
	API_VERSION = api_version
	SCOPES = [scope for scope in scopes[0]]

	cred = None

	pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
	# print(pickle_file)

	if os.path.exists(pickle_file):
		with open(pickle_file, 'rb') as token:
			cred = pickle.load(token)
			if not cred or not cred.valid:
				if cred and cred.expired and cred.refresh_token:
					cred.refresh(Request())
				else:
					flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
					cred = flow.run_local_server()

		with open(pickle_file, 'wb') as token:
			pickle.dump(cred, token)

	try:
		service = build(API_SERVICE_NAME, API_VERSION, credentials=cred, static_discovery=False)
		print(API_SERVICE_NAME, 'service created successfully')
		return service
	except Exception as e:
		print(e)
		return None
def downloader(name, pic_url):
	print(f"Downloading Media Item: {name}, from url {pic_url[:69]}")
	response = requests.get(pic_url, stream=True)
	if not response.ok:
		print(pic_url)
		print(response)
		return False
	handle= open(str(name), 'wb')
	for block in response.iter_content(1024):
		if not block:
			break
		handle.write(block)
	return True

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
##results is a dict
results = service.albums().list(pageSize=10).execute()
##albums is a list
albums= results['albums']
print(f"No.of Albums: {len(albums)}")
for album in albums:
	print()
	alb_id=album['id']
	title=album['title']
	myalb=service.albums().get(albumId=alb_id).execute()
	for key,val in myalb.items():
		print(f"{key}: {val}")
	req_body = {
			"albumId": alb_id,
			"pageSize": 100,  # Max is 100
			"pageToken": "",
			}
	mediaitems=[]
	res= service.mediaItems().search(body= req_body).execute()
	print("progress: ", len(res['mediaItems']))
	mediaitems.extend(res['mediaItems'])
	while 'nextPageToken' in res:
		req_body['pageToken']=res['nextPageToken']
		res= service.mediaItems().search(body= req_body).execute()
		mediaitems.extend(res['mediaItems'])
		print("progress: ", len(mediaitems))
#		break
#	print(len(mediaitems))
#	for key, val in mediaitems[0].items():
#		print(f"{key}: {val}")
	for media in mediaitems:
		pic_url= media['baseUrl']
		name= dup_pic(media['filename'])
		meta= media['mediaMetadata']
		width, height= meta['width'], meta['height']
		pic_url= pic_url+ "=w{0}-h{1}".format(width,height)
#		print(pic_url)
		downloader(name, pic_url)	
#		break
#	break
