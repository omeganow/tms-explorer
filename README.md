# TMS Explorer

TMS Explorer was developed to assist with the data preprocessing of transcranial magnetic stimulation (TMS) as part of the study "Transcranial direct current stimulation (tDCS) and mindfulness meditation in fibromyalgia" in the "Non-invasive brain stimulation lab" (NBS) at the university medicine Göttingen (UMG) under Prof. Dr. rer. nat. Andrea Antal. PhD student Perianen Ramasawmy conducted the study in 2022/2023 and the software was developed based on his requirements.

[DRKS Study Information](https://drks.de/search/de/trial/DRKS00029024)

## Data Preparation
1. Open .cfs file in software Signal 1.4  
2. Go to File > Export As...
3. Choose the location to save new file
4. Change Datatype to: MATLAB data (*.mat)
5. Filename > structure: F00x_timePoint_measurement; e.g. F001_AC_LICI
6. Time points: BA (baseline); PM (post meditation training); AC (acute); LT (long term)
7. Click "save"
8. Make sure "All frames" under Frames are selected ![Screenshot Signal 1](/screenshot_signal_export_1.png)
9. Check both boxes ![Screenshot Signal 2](/screenshot_signal_export_2.png)

## Import and work with .mat files in TMS Explorer

1. Open folder and browse for patients data ![Screenshot Overview](/screenshot_overview.png)
2. All frames which need to be inspected is marked as yellow: those are the ones with noisy baselines (>0.05 mV) and those without TMS pulses ![Screenshot Inspector](/screenshot_inspector.png)
3. After exclusion, the frames will be marked red.
4. Going back to the overview, all mean values has been adjusted to the current frames which hasn't been excluded. 

## Installation
>Make sure you have atleast Python 3.9 with virtualenv installed on your system. The requirements and virtual environment is set up automatically when running tms_explorer.sh/tms_explorer.bat

### MacOS and Linux
make the tms_explorer.sh file executable and execute it

    chmod +x tms_explorer.sh
    ./tms_explorer.sh

### Windows
run the tms_explorer.bat file either double clicking or running in terminal

    ./tms_explorer.bat

## Binaries
Additional you can find precompiled binaries for all platforms are distributed on github as well. 
#Todo: Add Link

