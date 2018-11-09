Nov 2018
============

Building object tracker workspace for ping pong ball.

Multiple utilities (alpha version) for recording, viewing, and characterizing video data from a consumer webcam. These are used to build and organize training/evaluation data which can be used to tune object tracker algo's for a desired task and time/accuracy characteristics.

The directory data/ in this repository corresponds to the ppd_data repository here: https://github.com/sutt/ppd_data

See documentation for the utility scripts here: https://github.com/sutt/ppd/tree/master/docs


Quickstart
============

    git clone https://github.com/sutt/ppd.git
    
    cd ppd
    rm data/ -r
    git clone https://github.com/sutt/ppd_data.git data

    cd test/
    pytest -vv     (some tests need a webcam available and will use it)

**To view a simple example**:

    python guiview.py --file data/proc/tmp/demo-agenda/output4.proc2.avi --showscoring

    (use gui ('Tracking' to On) to turn on tracking and visually evaluate performance)

**requirements:**

    python 2.7.13

    numpy 1.14.5+mkl
    opencv-contrib-python 3.2.0.8
    matplotlib  2.0.1
    pytest      3.3.2
    imutils     0.4.3
    Tkinter     revision 81008

    (windows supplementary .dll's)
    [not sure which one right now]
    openh264-1.4.0-win32msvc.dll
    openh264-1.4.0-win64msvc.dll
    opencv_ffmpeg320_64.dll
    opencv_ffmpeg320.dll
    
    (optional:)
    jupyter
    Flask
    any others?




