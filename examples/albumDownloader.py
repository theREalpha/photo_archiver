from src.service import Create_Service
from src.utility import album_retriever

API_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
##results is a dict
results = service.albums().list(pageSize=10).execute()
##albums is a list
albums= results['albums']
print(f"No.of Albums: {len(albums)}")
for i in range(len(albums)):
	print(f"{i+1}. {albums[i]['title']} : No. of Items- {albums[i]['mediaItemsCount']}")
print(f"{i+2}. All Albums")
albnum=int(input("Enter album number to be downloaded(0 to exit): "))
while albnum>len(albums)+1:
	print("Incorrect Album Number")
	albnum=int(input("Enter album number to be downloaded: "))
if albnum<=0:
	print("Exiting")
	exit()
elif albnum==len(albums)+1:
	for album in albums:
		album_retriever(album, service)
	exit()
else:
	album=albums[albnum-1]
	print(album)
	mediaList=album_retriever(service,album,includePhotos=False)
	print(len(mediaList))
