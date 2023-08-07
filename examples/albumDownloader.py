from src.service import Create_Service
from src.utility import logger,album_retriever,list_album,downloader

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

albums= list_album(service)
logger.info(f"No.of Albums: {len(albums)}")
for idx,album in enumerate(albums,start=1):
	print(idx,". ",album)
print(f"{idx+1}. All Albums")
num=len(albums)
albumIdx=num+2
while albumIdx>num+1:
	try:
		albumIdx=int(input("Enter album number to be downloaded(0 to exit): "))
		if albumIdx<=0: raise ValueError(albumIdx)
		if albumIdx>num+1:
			logger.error(f"Incorrect Album Number received, Please enter value b/w 0, {num+1}")
	except ValueError as e:
		logger.error(f"{e.args[0]} received, exiting")
		exit()
	except KeyboardInterrupt:
		logger.error("\nKeyboard Interrupt received, exiting")
		exit()

if albumIdx==len(albums)+1:
	for album in albums:
		response=album_retriever(service,album)
		mediaList,processingList=response['mediaItems'],response['processingItems']
		response=downloader(mediaList,threading=True)
		logger.info(f"{response['count']} items retrieved sucessfully")
		if len(processingList):
			logger.error(f"{len(processingList)} Items stuck in processing:\n{processingList}")
		if len(response['failed']):
			logger.error(f"{len(response['failed'])} Items failed:\n{response['failed']}")

else:
	album=albums[albumIdx-1]
	logger.info(album)
	response=album_retriever(service,album)
	mediaList,processingList=response['mediaItems'],response['processingItems']
	response=downloader(mediaList,threading=True)
	logger.info(f"{response['count']} items retrieved sucessfully")
	if len(processingList):
		logger.error(f"{len(processingList)} Items stuck in processing:\n{processingList}")
	if len(response['failed']):
		logger.error(f"{len(response['failed'])} Items failed:\n{response['failed']}")