import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import requests
import time
#import pandas as pd
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
	print(f"Downloading Media Item: {name}, from url {pic_url[:69]}...")
	response = requests.get(pic_url, stream=True)
	if not response.ok:
		print("failed download for url\n",pic_url)
		print("with response",response)
		return False
	handle= open(str(name), 'wb')
	for block in response.iter_content(1024):
		if not block:
			break
		handle.write(block)
	return True

def main():
	service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
	##results is a dict
	results = service.albums().list(pageSize=10).execute()
	##albums is a list
	albums= results['albums']
	print(f"No.of Albums: {len(albums)}")
	for i in range(len(albums)):
		print(f"{i+1}. {albums[i]['title']} : No. of Items- {albums[i]['mediaItemsCount']}")
	albnum=int(input("Enter Number for the album to be downloaded: "))
	if albnum<=0:
		print("Exiting")
		return
	while albnum>len(albums):
		print("Incorrect Album Number")
		albnum=int(input("Enter Number for the album to be downloaded: "))
		
	album=albums[albnum-1]
	print()
	alb_id=album['id']
	title=album['title']
	myalb=service.albums().get(albumId=alb_id).execute()
	#for key,val in myalb.items():
	#	print(f"{key}: {val}")
	req_body = {
			"albumId": alb_id,
			"pageSize": 100,  # Max is 100
			"pageToken": "",
			}
	mediaitems=[]
	res= service.mediaItems().search(body= req_body).execute()
	print("fetching progress: ", len(res['mediaItems']))
	for i in range(len(res['mediaItems'])):
		media= res['mediaItems'][i]
		meta= media['mediaMetadata']
		while ('video' in meta) and (meta['video']['status']=='PROCESSING'):
			print(f"sleeping to process {media['filename']}", i)
			time.sleep(1)
			res= service.mediaItems().search(body= req_body).execute()
			meta=res['mediaItems'][i]
#			print(meta)
	mediaitems.extend(res['mediaItems'])
	while 'nextPageToken' in res:
		req_body['pageToken']=res['nextPageToken']
		res= service.mediaItems().search(body= req_body).execute()
		for i in range(len(res['mediaItems'])):
			media= res['mediaItems'][i]
			meta= media['mediaMetadata']
			while ('video' in meta) and (meta['video']['status']=='PROCESSING'):
				print(f"sleeping to process {media['filename']}", i)
				time.sleep(1)
				res= service.mediaItems().search(body= req_body).execute()
				meta=res['mediaItems'][i]
#				print(meta)
		mediaitems.extend(res['mediaItems'])
		print("fetching progress: ", len(mediaitems))
#		break

	processing=[]
	count=0
	for media in mediaitems:
		media_url= media['baseUrl']
		name= dup_pic(media['filename'])
		meta= media['mediaMetadata']
		if ('video' in meta) and (meta['video']['status']=='PROCESSING'):
			print(f"\n\n\n {media['filename']} failed at processing stage \n\n\n")
			processing.append(media)
			continue	
		if 'photo' in meta:
			width, height= meta['width'], meta['height']
			media_url= media_url+ "=w{0}-h{1}".format(width,height)
		elif 'video' in meta:
			media_url= media_url+ "=dv"	
#			print(media_url)
		if downloader(name, media_url):
			count+=1
#		break
	print(f"""
			Total:  \t{len(mediaitems)}
			Success:\t{count}
			Failed: \t{len(mediaitems)-count}
			Failed due to Processing->{len(processing)}""")
#	kk= pd.DataFrame(mediaitems)
#	kk=kk.drop(['productUrl','id'], axis=1)
#	k2=kk[kk['mimeType']=='video/mp4']

if __name__=='__main__':
	main()
