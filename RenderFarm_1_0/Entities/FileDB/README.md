# File Mgmt

## Overview:
This submodule is for running a hash based file database (ledger and store) and exposure of spaces-files (exports & views) either locally or interfaced over the network using a flask blueprint api (submodule) and client instance (submodule).

The primary use case for a system like this is creating and storing files & folders on command for use in other applications, while preventing any duplicate information from existing, thereby preventing bloat from duplicate files.

As it's not a conventional file system, files are retained as long as there are users for them, and files when removed from the database are removed from the disk.

It's core components are:
- Files
  - Unnamed Sha256 hashed files, Referenced into spaces with names
  - Users: (Spaces) 
- Spaces
  - Unnamed DB folders that contain (namedSpaces) and (namedFiles)
  - Users: (Spaces),(Files),(Views),(Exports)
- Views 
  - Direct User: (Session)
  - session-temporary exports of a space to disk.
  - Untracked folder structure (Make sure to clean up after session closes!) 
- Export
  - Direct User : (Session),(User)
  - Semi-Perm 
  - Untracked folder structure, but tracked as a user of spaces
- Session
  - Direct User : (User)
  - Contains    : (SubUsers|Clients)
  - Contains    : (Views),(Exports)
  - Represents a topic/compute task focused Session
    - Usefull in tying to a compute jobs lifespace
  - Required for interacting with the db, as it acts as a buffer for a user
- User
  - Perm
  - Contains    : (Sessions),(Exports)
  - representative of a user entry. Not meant to contain secrets or similar
- Sub-user|Client-Actor
  - A seperate node acting indirectly on behalf of a user
  - Should be verified via middleware running this on a server

All of these are represented by repos operate using a context variable system that affects 
- Sessions
- Settings

Based on the contextual information of session, user & subuser|clientActor


