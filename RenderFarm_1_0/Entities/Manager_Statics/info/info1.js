var ws = new WebSocket(`ws://${window.location.host}/state-info`);
ws.onmessage = function(event) {

    var message = JSON.parse(event.data)

    const message_id = message[0]
    const topic      = message[1]
    const command    = message[2]
    // const yet       = message[3]

    const catagory   = message[3][0]
    const payload    = message[3][1]

    console.warn(`Getting command: ${JSON.stringify(message)}`)
    
    var tableBody = document.getElementById(`${catagory}-table`)
    if (!tableBody){
        console.warn(`Table Was not Found!! .${catagory}-table`)
        return
    }

    switch (command){
        case "BULK_CREATE":{
            payload.forEach((payload_item) =>{
                Create(tableBody,payload_item)
            })
            break
        }
        case "CREATE":{
            Create(tableBody,payload)
            break
        }

        case "UPDATE":{
            Update( tableBody, payload)
            break
        }

        case "DELETE":{
            Delete(tableBody,payload)
            break
        }

        default:{
            console.warn(`Failure to parse command: ${command} \n ... ${catagory} \n ... ${payload}`)
        }
    }
};


function Find(tableBody, uid){
    return tableBody.querySelector(`tr[data-id="${uid}"]`)
}


function Create(tableBody, payload){
    const row = tableBody.insertRow()
    row.dataset.id = payload.uid
    row.innerHTML = `
    <td class="uid">${payload.uid}</td>
    <td class="host">${payload.host}</td>
    <td class="port">${payload.port}</td>
    <td class="connection_state">${payload.con_state}</td>
    <td class="action_state">${payload.action_state}</td>
    `
}

function Delete(tableBody,payload){
    const item = Find(tableBody,payload.uid)
    if ( item ){ item.remove() }
}

function Update(tableBody,payload){
    const item = Find(tableBody,payload.uid)
    if (! item){
        console.warn(`Failure to find item to update: ... ${tableBody} \n ... ${payload.uid}`)
    }else{
        Object.entries(payload).forEach(([key,value]) => {
        if ( item ){
            column = item.querySelector(`.${key}`)
            if (column){
                column.textContent = value
            }
        }
    })}
}