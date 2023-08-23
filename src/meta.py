import piexif
from datetime import datetime
from src.objects import MediaItem
from src.logger import logger

def write_metadata(media: MediaItem, path: str) -> bool:
    '''
    Writes metadata to a media item.

    This function takes a MediaItem object representing media metadata and a file path,
    and writes the relevant metadata to the image file at the specified path.
    Note: works only for jpg, webp, tiff formats currently
    Parameters:
        media (MediaItem): A MediaItem object containing metadata.
        path (str): The path to the image file where metadata will be written.

    Returns:
        bool: True if metadata is successfully written, False otherwise.
    '''

    allowed=['jpg','jpeg','webp','tiff']
    if media.extension not in allowed:
        logger.error(f"Invalid filetype {media.extension} for writing metadata")
        return False

    meta = media.mediaMetadata
    exif_dict = {"0th": {}, "Exif": {}}

    exif_dict["0th"][piexif.ImageIFD.ImageWidth] = int(meta['width'])
    exif_dict["0th"][piexif.ImageIFD.ImageLength] = int(meta['height'])

    creation_time = datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.now() - datetime.utcnow()
    adjusted_creation_time = creation_time + delta
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = adjusted_creation_time.strftime("%Y:%m:%d %H:%M:%S")

    meta = meta['photo']
    if 'cameraMake' in meta:
        exif_dict["0th"][piexif.ImageIFD.Make] = meta['cameraMake'].encode('utf-8')
    if 'cameraModel' in meta:
        exif_dict["0th"][piexif.ImageIFD.Model] = meta['cameraModel'].encode('utf-8')
    if 'exposureTime' in meta:
        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (int(float(meta['exposureTime'][:-1])*1000000), 1000000)
    if 'isoEquivalent' in meta:
        exif_dict["Exif"][piexif.ExifIFD.ISOSpeedRatings] = [int(meta['isoEquivalent'])]
    if 'apertureFNumber' in meta:
        exif_dict["Exif"][piexif.ExifIFD.FNumber] = (int(float(meta['apertureFNumber'])*1000), 1000)
    if 'focalLength' in meta:
        exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (int(float(meta['focalLength'])*1000), 1000)

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, path)

    return True