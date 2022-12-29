## Service Imports
import pickle
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
## Auxilary Imports
import os
import time
import requests
from threading import Thread
## Declarations for Service creation
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

## @dup_pic: checks if a file with same name exists and returns name suffixed with an integer to avoid naming conflicts. ## assumes extensions are 3 letters
## ex: img.jpg, img_1.jpg, img_2.jpg exist in path. dup_pic('img.jpg') returns in such case 'img_3.jpg'
## args: name -> string type | name of the media file
## return value: name  -> string type => if a file with same name doesn't exist
##		 named -> string type => if a file with 'name' exists
def dup_pic(name):
	if os.path.isfile(name):
		i=1
		named=name[:-4]+"_"+str(i)+name[-4:]
		while os.path.isfile(named):
			i+=1
			named= name[:-4]+"_"+str(i)+name[-4:]
		return named
	return name
## @Create_Service: Creates a API service using google library. contains methods for accessing mediaitems, albums etc...
## args: client_secret_file -> string type | name of the file contating secret_key for the api
## return value: service | api POC
def Create_Service(client_secret_file, api_name, api_version, scopes):
	print(client_secret_file, api_name, api_version, scopes, sep='-')
	CLIENT_SECRET_FILE = client_secret_file
	API_SERVICE_NAME = api_name
	API_VERSION = api_version
	SCOPES = scopes

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

## @ThreadR: Inherited Thread class that can return value.
class ThreadR(Thread):
	def __init__(self, group=None, target=None, name=None,
			args=(), kwargs={}, Verbose=None):
		Thread.__init__(self, group, target, name, args, kwargs)
		self._return = None

	def run(self):
		if self._target is not None:
			self._return = self._target(*self._args,
							**self._kwargs)
	def join(self, *args):
		Thread.join(self, *args)
		return self._return

## @downloader: downloads the media from given url and saves it with the name provided
## args: name -> string type | name of the file to be downloaded
##	 media_url -> string type | url to the media 
## return value: False -> if response to download request is not 200 SUCCESS
##		 True -> if response is 200 SUCCESS and no error while writing to disk
def downloader(name, media_url):
	print(f"Downloading Media Item: {name}, from url {media_url[:69]}")
	response = requests.get(media_url, stream=True)
	if not response.ok:
		print(media_url)
		print(response)
		return False
	handle= open(str(name), 'wb')
	for block in response.iter_content(1024):
		if not block:
			break
		handle.write(block)
	return True
## @media_down: extracts url, name and meta_data requried for downloading the media item and prepares the url and passes it along to @downloader. Also checks for an ongoing issue with google api for 'PROCESSING' status videos and prevents from downloading it.
## args: media -> dict containing details, resources related to media item
##	 processing -> a list that tracks media items affected by google api issue
## return value: False -> if the media Item is affected with google api issue
##		       -> if the downloader function fails downloading
##		 True -> if downloader succeeds writing to disk
def media_down(media, processing):
	media_url= media['baseUrl']
	name= dup_pic(media['filename'])
	meta= media['mediaMetadata']
	if ('video' in meta) and (meta['video']['status']=='PROCESSING'):
		print(f"\n\n\n {media['filename']} failed at processing stage \n\n\n")
		processing.append(media)
		return False	
	if 'photo' in meta:
		width, height= meta['width'], meta['height']
		media_url= media_url+ "=w{0}-h{1}".format(width,height)
	elif 'video' in meta:
		media_url= media_url+ "=dv"	
#		print(media_url)
	return downloader(name, media_url)

def main():
	service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
	itemNum=int(input("Enter Number of items to download (0 -> to download all): "))
	if itemNum==0: numBool=True
	else: numBool=False
	results = service.mediaItems().list(pageSize=100).execute()	# results ->dict, with keys 'mediaItems' ->list , 'nextPageToken' ->string

##	checks if any media retrieved is still in "PROCESSING" state and waits for it to change to 'READY' state
	for i in range(len(results['mediaItems'])):
		media= results['mediaItems'][i]
		meta= media['mediaMetadata']
		while ('video' in meta) and (meta['video']['status']=='PROCESSING'):
			print(f"sleeping to process {media['filename']}", i)
			time.sleep(1)
			results= service.mediaItems().list(pageSize=100).execute()
			meta=results['mediaItems'][i]

	mediaList=[]								#list of mediaItems
	mediaList.extend(results['mediaItems'])
	print(f"No.of mediaItems retrieved: {len(mediaList)}")
	while ('nextPageToken' in results):
		if len(mediaList)>(itemNum) or numBool: break
		results = service.mediaItems().list(pageSize=100, pageToken=results['nextPageToken']).execute()
		pgtoken=results['nextPageToken']	
		for i in range(len(results['mediaItems'])):
			try: media= results['mediaItems'][i]
			except: print(i, len(results['mediaItems']))
			meta= media['mediaMetadata']
			while ('video' in meta) and (meta['video']['status']=='PROCESSING'):
				print(f"sleeping to process {media['filename']}", i)
				time.sleep(1)
				results = service.mediaItems().list(pageSize=100, pageToken=pgtoken).execute()
				meta=results['mediaItems'][i]

		mediaList.extend(results['mediaItems'])
		print(f"No.of mediaItems retrieved: {len(mediaList)}")
	
	thread_count= os.cpu_count()		## thread for each cpu core
	processing=[]				## to track media items affected by google api processing bug.
	count=0
	i=0
	## runs a loop with @thread_count threads downloading @thread_count media items in each thread.
	while i<=(len(mediaList)):
		threads=[]
		for k in range(thread_count):
			if i+k>= len(mediaList): break
			media = mediaList[i+k]
			threads.append(ThreadR(target= media_down, args=(media, processing)))
		for thread in threads:
			thread.start()
		for thread in threads:
			if thread.join():
				count+=1
		i+=thread_count
	
	print(f"""
			Total:  \t{len(mediaList)}
			Success:\t{count}
			Failed: \t{len(mediaList)-count}
			Failed due to Processing->{len(processing)}""")

if __name__=='__main__':
	main()
