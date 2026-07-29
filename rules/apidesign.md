Aim:
This Document defines the API Schema for both the frontend and the backend.

Constraints:
The keys in the data should always be lowercase.
The API endpoint should always denote its full intention.
Ex:

  1. If the user wants to log in, then the endpoint should be "/userlogin/".
  2. If the admin wants to log in, then the endpoint should be "/adminlogin/".
     Follow all the basic HTTP rules for `GET`, `POST`, `PUT`, `DELETE`, etc.

Status Codes:
200 for Success
404 for Admin pages
401 for Wrong credentials
402 for Payment failure
400 for Bad request

Error Handling:
Use a `report` key to provide the frontend with a clear reason for the result or error to display to the user.

Note:
The backend will also send the `report` key if the process is successful.
