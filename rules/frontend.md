
Aim:This document defines the frontend development rules to ensure consistency throughout the project.
Constraints:
* Follow the defined project folder structure.
* Reuse components whenever possible. Do not duplicate UI code.
* All API communication must be done through the `services` folder.
* All reusable functions must be placed in the `utils` folder.
* All configuration values must be stored in the `config` folder.
* Do not hardcode URLs, API endpoints, or constants.
* Every page must be placed inside the `pages` folder.
* Components must contain only UI-related logic whenever possible.
* Global state must be managed only through the `contexts` folder.
* Custom hooks must be placed inside the `hooks` folder.
* Static assets must be stored inside the `assets` folder.
* Follow the project's Naming Convention document.
* Follow the project's API Schema document.

Rules:
* One component should have one primary responsibility.
* Keep components modular and reusable.
* Avoid inline styles unless absolutely necessary.
* Keep business logic outside UI components whenever possible.
* Validate user input before sending API requests.
* Handle loading, success, and error states for every API request.
* Display backend `report` messages directly to the user whenever applicable in the failure . 
* Remove unused imports, variables, and components.
* Do not leave commented-out code.
* Do not hardcode sensitive information.
* Write clean, readable, and maintainable code.
* A proper comment shoudl be present at the top of the file to define the usecase of the files.
