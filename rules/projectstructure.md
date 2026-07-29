Aim:This document is about the project structure of the both backedn and the frontend 
Constraint:Complete isolation of endpoitn 
each folder and the file to be named in small letters
    - Each file shoudl denote its complete mening of the contens in it.
For the backend each endpoint needs to be saved in a single file 
    - With the common functions of all the files to saved in the common folder
    - IF the endpoint only need one function then it shoudl only be in the reative location of the endpoint file
For the frontend eaach page shoudl be saved in a single folder


Backend Folder structure -->
models-->Contaisn the database ,AI/ML models etc
routes--> Contains all the routes 
utills-->Contaisn all the common files and functions that are needed by more than 1 endpoint
config-->contaisn all the config files of the 
Frontend Folder Structure -->

Frontend  Folder structure -->
pages --> Contains all the pages/screens of the application.
components --> Contains all the reusable UI components used across multiple pages.
assets --> Contains images, icons, fonts, videos, and other static assets.
styles --> Contains all the global styles, themes, and common CSS files.
utils --> Contains all the common functions and utilities used across multiple components.
services --> Contains all the API calls and backend communication logic.
config --> Contains all the frontend configuration files
hooks --> Contains all the custom hooks used throughout the application
contexts --> Contains all the React Context providers and global state management.
layouts --> Contains all the reusable layouts shared by multiple pages.