# TMS Explorer

TMS Explorer was developed to assist with the preprocessing of transcranial magnetic stimulation (TMS) data as part of the study "Transcranial direct current stimulation (tDCS) and mindfulness meditation in fibromyalgia" in the "Non-invasive brain stimulation lab" (NBS) at the University Medicine Göttingen (UMG) under Prof. Dr. rer. nat. Andrea Antal. PhD student Perianen Ramasawmy conducted the study in 2022/2023 and the software was developed based on his requirements. The software was programmed by Oscar Moschner and Thuy Tien Mai.


#
More information can be found here:

[DRKS Study Information](https://drks.de/search/de/trial/DRKS00029024)

[Klinik für Neurologie UMG](https://neurologie.umg.eu)


## Data preparation
1. Open .cfs file in software Signal 1.4  
2. Go to File > Export As...
3. Choose the location to save new file
4. Change datatype to: MATLAB data (*.mat)
5. Filename > structure: F00X_timePoint_measurement; e.g. F001_AC_LICI
6. Time points: BA (baseline); PM (post meditation training); AC (acute); LT (long term)
7. Click "save"
8. Make sure "All frames" under Frames are selected
 
    ![Screenshot Signal 1](/img/screenshot_signal_export_1.png)
9.  Check both boxes
    
    ![Screenshot Signal 2](/img/screenshot_signal_export_2.png)

10. The files have to be put into a folder structure RootFolder -> F00X -> F00X_AC_LICI.mat

## Import and work with .mat files in TMS Explorer

UI overview with important elements marked

   ![Screenshot Overview](/img/screenshot_overview.png)


1. Open the root folder where you have exported the data  by clicking "browse". Wait a few seconds for the data to be imported.

2. The Overview will be automatically updated with the the selected patient. Use the "Patientlist" to select a new patient.

3. To inspect the frames use the "Tab Navigator" and select inspector. Here all frames which need to be inspected are marked as yellow: those are the ones with noisy baselines (>0.05 mV) and those without TMS pulses. 
 
    ![Screenshot Inspector](/img/screenshot_inspector.png)
   
4. After exclusion, the frames will be marked red. The selection which frames are rejected are saved in a hidden file within the folder "F00X/.rejected".

5. Going back to the overview, all mean values have been adjusted to the current frames which haven't been rejected.
   
6. When done inspecting the data of all patients and choosing the most suitable regression model for each recruitment curve. The data of all patients can be exported using one of the "Export Options".

## Installation
>Make sure you have atleast Python 3.9 and virtualenv installed on your system. The requirements and virtual environment is set up automatically when running tms_explorer.sh/tms_explorer.bat. If you are new to python or not used to operate the terminal see also these links:

[Python PIP](https://packaging.python.org/en/latest/tutorials/installing-packages/)
[Terminal Introduction](https://cs.colby.edu/maxwell/courses/tutorials/terminal/)



### General

   1. Clone the github repository or download and unzip
   2. Open a terminal and change directory (cd) into the repository
   3. Based on your Operating system run the commands below

### MacOS and Linux
make the tms_explorer.sh file executable and execute it

    chmod +x tms_explorer.sh
    ./tms_explorer.sh

### Windows
run the tms_explorer.bat file either double clicking or running in terminal

    ./tms_explorer.bat

## Binaries
In the future you can find precompiled binaries for all platforms on github. 