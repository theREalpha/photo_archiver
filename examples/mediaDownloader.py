from src.service import Create_Service
from src.utility import logger,media_retriever,downloader

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

response=media_retriever(service,limit=225)
mediaList,processingList=response['mediaItems'],response['processingItems']
response=downloader(mediaList,threading=True)

logger.info(f"{response['count']} items retrieved sucessfully")
if len(processingList):
	logger.error(f"{len(processingList)} Items stuck in processing:\n{processingList}")
if len(response['failed']):
	logger.error(f"{len(response['failed'])} Items failed:\n{response['failed']}")