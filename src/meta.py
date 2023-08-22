from PIL import Image
from src.objects import MediaItem
from src.logger import logger
from PIL import ImageFile
from datetime import datetime
ImageFile.LOAD_TRUNCATED_IMAGES = True

def write_metadata(media: MediaItem, path: str)->bool:
    '''
    Writes metadata to a media item.

    This function takes a MediaItem object representing media metadata and a file path,
    and writes the relevant metadata to the image file at the specified path.
    Note: Currently only works for images, and only camera make, model is written properly
    Parameters:
        media (MediaItem): A MediaItem object containing metadata.
        path (str): The path to the image file where metadata will be written.

    Returns:
        bool: True if metadata is successfully written, False otherwise.
    '''

    meta=media.mediaMetadata
    exif=Image.Exif()
    time_obj = datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.datetime.now()- datetime.datetime.utcnow()
    time_obj = time_obj + delta
    formatted_time = time_obj.strftime("%Y:%m:%d %H:%M:%S")

    exif[256]= int(meta['width'])
    exif[257]= int(meta['height'])
    exif[306]= formatted_time

    if media.is_photo():
        meta=meta['photo']
        exif[271]= meta.get('cameraMake','')
        exif[272]= meta.get('cameraModel','')
        if 'exposureTime' in meta: exif[33434]= float(meta['exposureTime'][:-1])
        if 'isoEquivalent' in meta: exif[34855] = int(meta['isoEquivalent'])
        if 'apertureFNumber' in meta: exif[37378] = int(meta['apertureFNumber'])
        if 'focalLength' in meta: exif[37386] = int(meta['focalLength'])
    else:
        exif[51044]= float(meta['video']['fps'])
    try:
        handle=Image.open(path)
    except:
        logger.error(f"Cannot write metadata for the file:{media.filename}")
        return False
    handle.save(path,exif=exif)
    return True