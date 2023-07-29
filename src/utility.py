import os
import time
import requests
from threading import Thread
from multiprocessing.pool import ThreadPool
from src.service import Create_Service

RETRY_LIMIT = 1

'''
Extention of builtin Thread class to return value once exited.
'''
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
    

def dup_pic(name):
    if not os.path.isfile(name):
        return name
    i=1
    ext=name.rfind('.')
    newName=name[:ext]+"_"+str(i)+name[ext:]
    while os.path.isfile(newName):
        i+=1
        newName= name[:-4]+"_"+str(i)+name[-4:]
    return newName


def downloader(name, mediaURL):
    print(f"Downloading Media Item: {name}, from url {mediaURL[:69]}...")
    response = requests.get(mediaURL, stream=True)
    if not response.ok:
        print("failed download for url\n", mediaURL)
        print("with response",response.json())
        return False
    handle= open(str(name), 'wb')
    for block in response.iter_content(1024):
        if not block:
            break
        handle.write(block)
    return True

def media_down(media: dict, badItems:list):
    mediaURL= media['baseUrl']
    name= dup_pic(media['filename'])
    meta= media['mediaMetadata']
    if ('video' in meta) and (meta['video']['status']=='PROCESSING'):
        print(f"\n\n\n {media['filename']} failed at processing stage \n\n\n")
        badItems.append(media)
        return False    
    if 'photo' in meta:
        width, height= meta['width'], meta['height']
        mediaURL= mediaURL+ "=w{0}-h{1}".format(width,height)
    elif 'video' in meta:
        mediaURL= mediaURL+ "=dv"    
#        print(media_url)
    return downloader(name, mediaURL)

def download_stager(items: list, threading: bool=True, threadCount: int= os.cpu_count(), batching: bool=False) -> bool:
        '''
        ToDo: batching
        '''
        
        processing=[]
        count=0
        
        if not threading:
            for media in items:
                if media_down(media,processing):
                    count+=1
        
        else:
            helper = lambda item: media_down(item,processing)
            with ThreadPool() as pool:
                print(f"No.of threads running: {pool._max_workers-4}")
                count+=pool.map(helper, items, chunksize= (len(items)//(pool._max_workers-4)+1)).count(True)
            
        print(f"""
                Total:  \t{len(items)}
                Success:\t{count}
                Failed: \t{len(items)-count}
                Failed due to Processing->{len(processing)}""")

def album_retriever(service: Create_Service, album: dict, limit: int=0, pageToken: str="", includePhotos: bool= True, includeVideos: bool= True) -> list:
    '''
    Func: album_retriever
    Input:
        service: API service object
        album: a dictionary item containing id, mediaCount, mediaCover etc...
        limit: int. Default value set to albums mediaCount.
        pageToken: str. Default value set to '' to retrieve first page of album if no pageToken is given
    Output:
        Returns a list of media Items.
    '''
    albumId, albumTitle = album['id'], album['title']
    
    print(f"\nRetrieving Album: {albumTitle} with ID: {albumId}") 

    mediaItems=[]
    if not limit: limit = int(album['mediaItemsCount'])
    pageSize = limit if limit<=100 else 100         # Max limit per page is 100
    counter=0
    while True:
        counter+=1
        req_body = {
                "albumId": albumId,
                "pageSize": pageSize,  
                "pageToken": pageToken,
                }
        
        response = service.mediaItems().search(body= req_body).execute()
        response['mediaItems']=[item for item in response['mediaItems'] if (includePhotos and 'photo' in item['mediaMetadata']) or (includeVideos and 'video' in item['mediaMetadata'])]
        retrievedNum= len(response['mediaItems'])
        print(f"#{counter} Fetching progress: {retrievedNum}")
        if includeVideos:
            for i in range(retrievedNum):
                media= response['mediaItems'][i]
                metaData= media['mediaMetadata']
                retryCount= RETRY_LIMIT

                while metaData.get('video') and (metaData['video']['status']=='PROCESSING') and retryCount:
                    print(f"sleeping to process {media['filename']}", i)
                    time.sleep(1)
                    response= service.mediaItems().search(body= req_body).execute()
                    response['mediaItems']=[item for item in response['mediaItems'] if (includePhotos and 'photo' in item['mediaMetadata']) or (includeVideos and 'video' in item['mediaMetadata'])]
                    meta=response['mediaItems'][i]
                    retryCount-=1
        
        limit -= retrievedNum
        print("limit: ", limit)
        if limit<0: 
            mediaItems.extend(response['mediaItems'][:100+limit])
            return mediaItems
        print("total: ", len(mediaItems))
        mediaItems.extend(response['mediaItems'])
        
        if not response.get('nextPageToken'): 
            return mediaItems
       
        pageToken= response.get('nextPageToken','')