#-----------------------------------------------------------------------------
# Copyright (c) 2013-2019, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------


import os

#add the path to nltk_data
os.environ["NLTK_DATA"] = os.path.join(sys._MEIPASS, "nltk_data")
