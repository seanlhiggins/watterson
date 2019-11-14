<b>Owner: Sean Higgins</b>
</br>
<b>Date</b>: 5/11/19
</br>
<b>Brief</b>: Build a small portal that will allow an admin to upload a .csv file to create and manage Looker users. 

The portal will read the headers from the CSV and expect one column to be an email and the rest to be other data types. Those that are not email columns will be used for User Attributes. The user will be able to select which columns are used. The portal will validate the names of headers against User Attributes that already exist. The portal will use Looker’s API to set or update a user’s User Attribute value based on the corresponding cell value in the CSV.  

A later iteration will also incorporate Groups. Again the portal will read the headers of the CSV and the user will select whether the column is to be used for a Group or User Attribute. 

<b>Goal</b>: The aim of this is to have an easier way for Looker Admins to manage users, using CSV uploads and an offline spreadsheet that’s easy to read and edit. Circumventing Looker’s very cumbersome user management workflows and having a single element that coalesces Groups, Users and Attributes to a single action that obfuscates the API workflow we typically have to train people on when they want a single flow. 

<b>Build</b>: I’ll likely build this with a Python backend so I can use Pandas which is good for reading csvs and creating dataframes that a) hold data in an easy to understand structure and b) be easily parsed for firing off requests

<b>Update (7/11/19)</b>: Spent a few days just creating the basic building blocks in terms of functions and calls to interpret what a user provides in a CSV to turn into Looker logic. Figuring out the edges of calls and helper functions needed later to make things work. 

<b>Update (10/11/19)</b>: Did a bit of cleanup, prepped some stuff via Pandas so the eventual UI will have what it needs to construct an interface for selection of columns etc. Added a bunch of TODOs to keep a breadcrumb trail and keep focus on what's needed next.

<b>Update (14/11/19)</b>: Using Flask to make a simple app with UI for uploading csv, cleaned up some references, removed hardcoded stuff. Nothing fancy. 