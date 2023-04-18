""" 
TMS Explorer was developed to assist with the data preprocessing of transcranial 
magnetic stimulation (TMS) as part of the study "Transcranial direct current 
stimulation (tDCS) and mindfulness meditation in fibromyalgia" in the "Non-
invasive brain stimulation lab" (NBS) at the university medicine Göttingen (UMG) 
under Prof. Dr. rer. nat. Andrea Antal. PhD student Perianen Ramasawmy conducted 
the study in 2022/2023 and the software was developed based on his requirements.

[DRKS Study Information](https://drks.de/search/de/trial/DRKS00029024)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.

Authors: O. Moschner, T.T. Mai
"""


import sys

from PyQt6 import QtWidgets
from tms_ui import TmsUi


app = QtWidgets.QApplication(sys.argv)
window = TmsUi(app)
window.show()
app.exec()
