<!-- 
This file Is the TD Log for me as a solo dev. 
Any new features/Planned things go in the backlog. 
Any thing I work on daily I copy to current day and work on it adding time to current time at the end. If not completed it's coppied back to the top of the backlog and picked up again another day, or the tasks are re-scoped.

Time estimatations follow this format :
    - [ ] {est_time}{@current_time}{branch} Task
    ie:
    - [X] {~10hr}{@5hr}{dev} Converting X to Y
    - [ ] {~1hr}{@2hr}{bug->main} Fix bug xyz

Landmarks are goalposts/Features. Usually anagous with a dev branch.
-->

# Landmarks
## File Mgmt
WIP
br: f_mgmt
A file managment system that can be run locally or via a manager(flask) and clients. Assumption of middleware in manager to gate requests. Middleware out of scope of landmark.

## Graph & Node Types
TD
br: types
clarify types and basic struct 
- Core execution flow init implimented here as well
- meta-nodes, exec-nodes, socket-ref, exec-manifest defined.

## Py Module Exposure
TD
br: py_expose
Add an api for delayed and declarative node & graph creation in node format.
- Consider implimenting a (py-ffmpeg fluent) like interface.

## Save and Open
TD
br: save
Standard API for saving and loading files w/ graph/node types
- Type as an argument, future allowences for .tcsn & similar.
- Base is json-msg pack. Adding things to types may be required.

## Defered Collapse meta nodes
TD
br: collapse
Add Repeat, Multi and other defered types

## Manager, Client 
TD
br: net_base
Add io for exposing the manager and client relation and distributing tasks
- Will have to add job zones/jobs and deliniation of collapse when/where
- Uncertain application direct, will be clarified via previous landmarks and will update here w/a


# Daily

## 2025-06-24

- [x]{~1hr}{@1hr}{main} Setup repo, add TD and some landmarks
- [x]{~.25hr}{@0hr}{main} copy over diagrams
- [ ]{~2hr}{@0hr}{f_mgmt} Add fundimental managment utils (sqlite, recur file/folder hashing)


# Backlog:
- [ ]{~2hr}{@0hr}{f_mgmt} Add Secondary interface to mgmt utils (putting sqlite to the file hashing, storing and retrieving spaces-files)
- [ ]{~1hr}{@0hr}{main} Clarify order of operations in [[structure]]