# Command Line Twitch Prediction Manger

A simple program to automate the setting (of names) and starting/creating of predictions for matches.

## How to use
Assuming you have python and the required libraries installed, before launching:

1. [Make a twitch dev application](https://dev.twitch.tv/console).   
1.1 Set the redirect Uri to `http://localhost:3000` (or the port of your choice)  
1.2 make sure to keep note of the client id, client secret.
2. open predictionManager.py in your IDE/text editor of choice
3. Fill in the information for your twitch information in the constants section.  
3.1  For the TSH_FOLDER, put in the full path to the root of your [Tournament Stream Helper](https://github.com/joaorb64/TournamentStreamHelper) Folder
4. Run the program in your terminal (`python predictionManager.py`)
5. At launch it should open a window for you to log in with your twitch, log in and the window should close once successful.
6. Back in the terminal, a menu of options should be displayed.