from src.service import Create_Service
from src.utility import album_retriever,list_album,downloader
from src.objects import AlbumItem
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
##results is a dict
#results = service.albums().list(pageSize=10).execute()
##albums is a list
#albums= list(map(albumItem, results['albums']))
albums= list_album(service)
print(f"No.of Albums: {len(albums)}")
for idx,album in enumerate(albums,start=1):
	print(idx,". ",album)
print(f"{idx+1}. All Albums")
num=len(albums)
albumIdx=num+2
while albumIdx>num+1:
	try:
		albumIdx=int(input("Enter album number to be downloaded(0 to exit): "))
		if albumIdx<=0: raise ValueError
		if albumIdx>num+1: print(f"Incorrect Album Number received, Please enter value b/w 0, {num}")
	except KeyboardInterrupt or ValueError:
		print("Exiting Application")
		exit()

if albumIdx==len(albums)+1:
	for album in albums:
		mediaList,processing=album_retriever(service,album)
		count=downloader(mediaList,threading=False)
		print(f"{count} items retrieved sucessfully")

else:
	album=albums[albumIdx-1]
	print(album)
	mediaList,processing=album_retriever(service,album)
	count=downloader(mediaList,threading=False)
	print(f"{count} items retrieved sucessfully") 
