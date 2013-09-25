
# got this code from StackOverflow:
# http://stackoverflow.com/questions/5137082/django-python-modules-and-git-submodules


#At the top of settings.py
import sys, os
git_sub_modules = 'packages'     #Relative paths ok too

this_dir, this_file = os.path.split( __file__ )
git_sub_modules_abs = os.path.join( this_dir, git_sub_modules )

for dir in os.listdir( git_sub_modules_abs ) :
    path = os.path.join( git_sub_modules_abs, dir )
    if not path in sys.path :
        sys.path.append( path )



""" imports """

import roadgeometry
import nxopt
import polyglint2d
import bpmatch_roads


import road_Ed
import roademd
import roademd_approx
import roademd_approx2
