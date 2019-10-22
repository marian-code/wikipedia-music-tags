#-----------------------------------------------------------------------------
# Copyright (c) 2005-2019, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------


# hook for lazy_import
from PyInstaller.utils.hooks import collect_data_files

# add datas for lazy_import
datas = collect_data_files('lazy_import', False)
