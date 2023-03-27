""" 
TMS Explorer - Was developed to help with the data preprocessiing of the
tdcs and mm meditation study and Universitätsmedizin Göttingen led by Prof.Antal
....


This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

Authors: O. Moschner, Thuy Tien Mai
"""

import sys

from PyQt6 import QtWidgets
from tms_ui import TmsUi


app = QtWidgets.QApplication(sys.argv)
window = TmsUi(app)
window.show()
app.exec()
