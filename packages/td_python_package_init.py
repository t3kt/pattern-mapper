import sys

if False:
	from ..common.lib._stubs import *

def init():
	pkgpath = project.folder + '/packages'

	if pkgpath not in sys.path:
		sys.path.append(pkgpath)

