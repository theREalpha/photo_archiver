# photo_archiver
A CLI Application for creating a backup copy or downloading media items uploaded to Google photos cloud.

Made using the RESTful Google Photos API in python.
Before Running make sure client_secret.json is placed in the directory with developers secret_key

Currently supports:  
-> main.py  
>	=> Application to run mediaDownloader or albumDownloader  

-> mediaDownloader.py  
>	=> Lists total number of media items found  
>	=> Downloading all media items ever uploaded or the specified amount given in prompt  
>	=> Supports Multithreading  

-> albumDownloader.py  
>	=> Lists the albums created by user and number of items in it  
>	=> Downloading specified album or all albums created by the user  
>	=> Supports Multithreading  

-> singleAlbumDownloader_st.py  
>	=> Lists the albums created by user and number of items in it  
>	=> Download the specified album only  

-> allAlbumDownloader_st.py  
>	=> Downloads all the albums created by user  
  
  
ToDo:  
>-> Add option to dowload media based on type  
>-> Creating Environment independent application  
