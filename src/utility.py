import os
import time
import requests
import logging
import sys
from multiprocessing.pool import ThreadPool

from src.service import Create_Service
from src.objects import AlbumItem, MediaItem

RETRY_LIMIT = 3
RETRY_WAIT = 5

PATH='downloads/'

##logging related start
VERBOSE = False
MODONLY= True
modDEBUG=11
logging.addLevelName(11, 'modDEBUG')
if VERBOSE and not MODONLY:
    LVL=logging.DEBUG
elif VERBOSE and MODONLY:
    LVL=11
elif not VERBOSE and MODONLY:
    LVL=logging.INFO
else:
    LVL=logging.ERROR

logging.basicConfig(stream=sys.stdout,level=LVL)
logger=logging.getLogger('Log')
logger.propagate=False

handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
##logging related end

def dup_pic(name)->str:
    '''
    Generates a new name for a file by appending an incremental number if the file already exists.

    Args:
        name (str): The original name of the file.

    Returns:
        str: A new name with an incremental number appended to it if necessary to avoid filename conflicts.
    '''
    if not os.path.isfile(name):
        return name
    i=1
    ext=name.rfind('.')
    newName=name[:ext]+"_"+str(i)+name[ext:]
    while os.path.isfile(newName):
        i+=1
        newName= name[:-4]+"_"+str(i)+name[-4:]
    return newName

def media_down(media: MediaItem)->int:
    '''
    Downloads the media content specified by checking for naming conflicts and preparing download url.

    Args:
        media (MediaItem): The MediaItem object representing the media to be downloaded.

    Returns:
        statusCode (int): returns the statusCode of request if Failed, else 0
    '''
    mediaURL= media.baseUrl
    path= dup_pic(PATH+media.filename)
    meta= media.mediaMetadata
    if media.is_photo():
        width, height= meta['width'], meta['height']
        mediaURL= mediaURL+ f"=w{width}-h{height}"
    elif media.is_video():
        mediaURL= mediaURL+ "=dv"

    try:
        response = requests.get(mediaURL, stream=True)
    except Exception as e:
        logger.error(f"Unknown error while processing request for id {media.id}. Exception:\n{e}")
        return -1
    logger.log(modDEBUG,f"Downloading Media Item: {media.filename}, size: {int(response.headers['Content-Length'])/(1024):.3f} KB")
    if not response.ok:
        logger.error(f"failed download for media {media.filename}\nid: {media.id} ")
        logger.error(f"with response {response}")
        return response.status_code
    handle= open(str(path), 'wb')
    for block in response.iter_content(1024):
        if not block:
            break
        handle.write(block)
    return 0

def downloader(items: list, threading: bool=True, threadCount: int= os.cpu_count()+4, batching: bool=False) -> dict:
    '''
    Downloads media items from the provided list through media_down.

    Args:
        items (list): A list of media items to be downloaded.
        threading (bool, optional): Set to True to use multi-threading, False to use a single thread. Default: True.
        threadCount (int, optional): The number of threads to use when multi-threading is enabled. Default: No. of CPU cores + 4.
        batching (bool, optional): ToDo: add download through batching. Default is False.

    Returns:
        dict: A dictionary containing the following key-value pairs:
              - 'count' (int): The number of media items successfully downloaded.
              - 'failed' (List[MediaItem]): A list of media items which failed.
    '''
    failed=[]
    if not threading:
        for media in items:
            if media_down(media):
                failed.append(media)

    else:
        with ThreadPool(threadCount) as pool:
            logger.log(modDEBUG,f"No.of threads running: {threadCount-4}")
            statusCodes=pool.map(media_down, items)

            for idx,code in enumerate(statusCodes):
                if code:
                    failed.append(items[idx])

    total,fail=len(items),len(failed)
    logger.info(f"""
            Total:  \t{total}
            Success:\t{total-fail}
            Failed: \t{fail}""")

    return {'count':total-fail,
            'failed': failed}

def list_album(service: Create_Service, limit: int = 50, pagetoken: str = '') -> list[AlbumItem]:
    '''
    Retrieves a list of album items using the provided API service.

    Args:
        service (Create_Service): An API service object.
        limit (int, optional): The maximum number of album items to retrieve. Default: 50.
        pagetoken (str, optional): To retrieve items from the given pageToken and forward. Default: "".

    Returns:
        list[AlbumItem]: A list of album items.
    '''

    albumList=[]
    pagesize=limit if limit<50 else 50
    while True:
        response= service.albums().list(pageSize=pagesize,pageToken=pagetoken).execute()
        albumList.extend(map(AlbumItem,response['albums']))
        if not response.get('nextPageToken'):
            return albumList
        if len(albumList)>limit: return albumList[:limit]
        pagetoken= response.get('nextPageToken')


def process_video(service: Create_Service, media: MediaItem)-> MediaItem:
    '''
    Resends a request for a media item that is stuck in processing RETRY_LIMIT times, with RETRY_LIMIT interval.

    Args:
        service (Create_Service): API service object.
        media (MediaItem): The media item that needs to wait for processing.

    Returns:
        MediaItem: After retrying to retrieve the media, returns the processed media if it's processed,
        otherwise, returns the original media item.
    '''
    metaData= media.mediaMetadata
    retryCount= RETRY_LIMIT

    while (metaData['video']['status']=='PROCESSING') and retryCount:
        logger.log(modDEBUG,f"sleeping to process {media}")
        time.sleep(RETRY_WAIT)
        response= service.mediaItems().get(mediaItemId=media.id).execute()
        metaData= MediaItem(response).mediaMetadata
        retryCount-=1
    return media

def album_retriever(service: Create_Service, album: AlbumItem,
                    limit: int=0, pageToken: str="",
                    includePhotos: bool= True, includeVideos: bool= True) ->dict[str:list[MediaItem]]:
    '''
    Retrieves list of media items from an album.

    Args:
        service (Create_Service): API service object.
        album (AlbumItem): An albumItem class mainly containing id, mediaCount, mediaCover, etc.
        limit (int, optional): Number of mediaItems to be retrieved. Default: mediaCount.
        pageToken (str, optional): To retrieve items from a given pageToken and forward. Default: "".
        includePhotos (bool, optional): Flag to set if photos need to be included. Default: True.
        includeVideos (bool, optional): Flag to set if videos need to be included. Default: True.

    Returns:
        dict: A dictionary containing the following key-value pairs:
              - 'mediaItems' (List[MediaItem]): A list of retrieved media items.
              - 'processingItems' (List[MediaItem]): A list of media items stuck in the processing stage.
    '''


    logger.info(f"Retrieving\n{album}")

    mediaItems=[]
    processingItems=[]
    if not limit: limit = int(album.mediaItemsCount)
    pageSize = min(limit,100)         # Max limit per page is 100
    counter=0
    while True:
        counter+=1
        req_body = {
                "albumId": album.id,
                "pageSize": pageSize,  
                "pageToken": pageToken,
                }

        response = service.mediaItems().search(body= req_body).execute()
        response['mediaItems'][:]= map(MediaItem, response['mediaItems'])
        response['mediaItems']=[item for item in response['mediaItems'] if (includePhotos and item.is_photo()) or (includeVideos and item.is_video())]

        for media in response['mediaItems']:
            if includeVideos and media.is_video() and media.mediaMetadata['video']['status']== 'PROCESSING':
                media=process_video(service,media)
                if media.mediaMetadata['video']['status']!= 'PROCESSING':
                    mediaItems.append(media)
                else:
                    processingItems.append(media)
            else:
                mediaItems.append(media)
        processed, needProcessing=len(mediaItems), len(processingItems)
        if limit<processed+needProcessing:
            mediaItems=mediaItems[:limit-needProcessing]
            return {'mediaItems':mediaItems,
                    'processingItems':processingItems}
        logger.log(modDEBUG,f"#{counter} Fetching: {processed} processed, {needProcessing} stuck in processing")
        logger.log(modDEBUG,f"Total media Retrieved: {len(mediaItems)}")

        if not response.get('nextPageToken'): 
            return {'mediaItems':mediaItems,
                    'processingItems':processingItems}

        pageToken= response.get('nextPageToken','')