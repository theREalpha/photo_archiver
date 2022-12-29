import multithread_albdown
import mediaDownloader

import sys

def helper(s):
	if s=='h':
		print("""
			Help: 
				For 		-> 	use commands
			## Media Downloader 	->	python3 main.py -m 
			## Album Downloader 	->	python3 main.py -a
			## This help		-> 	python3 main.py -h   	or	python3 main.py --help""")
	if s=='e':
		print("""
			Invalid Args: 
				For 		-> 	use commands
			## Media Downloader 	->	python3 main.py -m 
			## Album Downloader 	->	python3 main.py -a
			## Help			-> 	python3 main.py -h   	or	python3 main.py --help""")
	return


args= sys.argv[1:]
if len(args)!=1:
	helper('e')
	sys.exit()

else:
	if args[0]=='-h': helper('h')
	elif args[0]=='-m': mediaDownloader.main()
	elif args[0]=='-a': multithread_albdown.main()
	else:
		helper('e')
		sys.exit()

