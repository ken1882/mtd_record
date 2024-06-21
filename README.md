# MTD Recorder
Automated character story recording for monmusutd.

## Setups
1. Clone the repo
2. run `pip install -r requirements.txt`
3. Create a `.tmp` folder in project root directory
4. Install tesseract (https://github.com/tesseract-ocr/tesseract)
    * You must have Japanese language pack installed
    * Make sure tesseract is in your $PATH
5. Install OBS (https://obsproject.com/)
    * You'll need to enable websocket server
    * Edit the code for authentication or disable obs wss authentication (since its on localhost so should be fine)

## Run the recordings
* You must have DMM Player and the game installed
* The resolutions are hard coded at 1920x1080 with 100% zoom
* Run `python main.py rec` if you only want to record single story
    * Select the one you want to record the leave it at scene select window (cancel/start/red one)
* Run `python main.py rec -a` to automatically record all stories
    * Does not handle interruptions such as date changed or disconnect so be aware
    * Will take occuption of your mouse when click needed so better leave it run when you're AFK
