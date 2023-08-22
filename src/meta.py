import piexif
from datetime import datetime
from src.objects import MediaItem

def write_metadata(media: MediaItem, path: str) -> bool:
    '''
    Writes metadata to a media item.

    This function takes a MediaItem object representing media metadata and a file path,
    and writes the relevant metadata to the image file at the specified path.

    Parameters:
        media (MediaItem): A MediaItem object containing metadata.
        path (str): The path to the image file where metadata will be written.

    Returns:
        bool: True if metadata is successfully written, False otherwise.
    '''

    meta = media.mediaMetadata
    exif_dict = {"0th": {}, "Exif": {}}

    exif_dict["0th"][piexif.ImageIFD.ImageWidth] = int(meta['width'])
    exif_dict["0th"][piexif.ImageIFD.ImageLength] = int(meta['height'])

    creation_time = datetime.strptime(meta['creationTime'], "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.now() - datetime.utcnow()
    adjusted_creation_time = creation_time + delta
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = adjusted_creation_time.strftime("%Y:%m:%d %H:%M:%S")

    if media.is_photo():
        meta = meta['photo']
        exif_dict["0th"][piexif.ImageIFD.Make] = meta.get('cameraMake', '').encode('utf-8')
        exif_dict["0th"][piexif.ImageIFD.Model] = meta.get('cameraModel', '').encode('utf-8')
        if 'exposureTime' in meta:
            exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (int(float(meta['exposureTime'][:-1])*1000000), 1000000)
        if 'isoEquivalent' in meta:
            exif_dict["Exif"][piexif.ExifIFD.ISOSpeedRatings] = [int(meta['isoEquivalent'])]
        if 'apertureFNumber' in meta:
            exif_dict["Exif"][piexif.ExifIFD.FNumber] = (int(float(meta['apertureFNumber'])*1000), 1000)
        if 'focalLength' in meta:
            exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (int(float(meta['focalLength'])*1000), 1000)
    else:
        exif_dict["Exif"][piexif.ExifIFD.ExposureTime] = (1, int(meta['video']['fps']))

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, path)

    return True