class AlbumItem:
    def __init__(self, albumData:dict) -> None:
        self.id:str = albumData['id']
        self.title:str = albumData.get('title',"Untitled Album")
        self.productUrl:str = albumData['productUrl']
        self.mediaItemsCount:int = int(albumData.get('mediaItemsCount','0'))
        self.coverPhotoBaseUrl:str = albumData['coverPhotoBaseUrl']
        self.coverPhotoMediaItemId:str = albumData.get('coverPhotoMediaItemId',None)
    
    def __toJSON__(self)-> dict:
        jsonDict={}
        jsonDict['id'] = self.id
        jsonDict['title'] = self.title
        jsonDict['productUrl'] = self.productUrl
        jsonDict['mediaItemsCount'] = self.mediaItemsCount
        jsonDict['coverPhotoBaseUrl'] = self.coverPhotoBaseUrl
        jsonDict['coverPhotoMediaItemId'] = self.coverPhotoMediaItemId

        return jsonDict
    
    def __str__(self)-> str:
        return f"albumTitle: {self.title}, mediaCount: {self.mediaItemsCount}, id: {self.id}"
    def __repr__(self)-> str:
        return f"albumTitle: {self.title}, mediaCount: {self.mediaItemsCount}, id: {self.id}"
    
class MediaItem:
    __slots__ = ['id', 'productUrl', 'baseUrl', 'mimeType', 'mediaMetadata', 'filename',
                 'extension', 'mediaType','downloadURL']
    def __init__(self,media: dict) -> None:
        self.id:str = media['id']
        self.productUrl:str = media['productUrl']
        self.baseUrl:str = media['baseUrl']
        self.mimeType:str = media['mimeType']
        self.mediaMetadata:dict = media['mediaMetadata']
        self.filename:str = media['filename']
        self.extension:str= self.filename[self.filename.rfind('.')+1:].lower()
        self.mediaType:str = 'photo' if self.mimeType.startswith('image') else 'video'
        self.downloadURL:str = self.baseUrl+ f"=d" if self.mediaType=='photo' else self.baseUrl+"=dv"

    def __toJSON__(self) -> dict:
        jsonDict={}
        jsonDict['id'] = self.id
        jsonDict['productUrl'] = self.productUrl
        jsonDict['baseUrl'] = self.baseUrl
        jsonDict['mimeType'] = self.mimeType
        jsonDict['mediaMetadata'] = self.mediaMetadata
        jsonDict['filename']     = self.filename
        jsonDict['extension']    = self.extension
        jsonDict['mediaType']    = self.mediaType
        jsonDict['downloadURL']  = self.downloadURL
        return jsonDict

    def is_video(self)-> bool: return self.mediaType=='video'
    def is_photo(self)-> bool: return self.mediaType=='photo'
    
    def __str__(self)->str:
        return f"mediaName: {self.filename}, mediaType: {self.mediaType}, id: {self.id}"
    def __repr__(self)->str:
        return f"mediaName: {self.filename}, mediaType: {self.mediaType}, id: {self.id}"