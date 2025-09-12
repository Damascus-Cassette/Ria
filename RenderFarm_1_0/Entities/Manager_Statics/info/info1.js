var ws = new WebSocket(`ws://${window.location.host}/state-info`);
ws.onmessage = function(event) {

    var message = JSON.parse(event.data)

    const command  = message[0]
    const catagory = message[1]
    const payload  = message[2]

        console.warn(`Getting command: ${command} ${catagory} \n ... id: ${payload.id} \n ... label: ${payload.label}`)
    
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


function Find(tableBody, id){
    return tableBody.querySelector(`tr[data-id="${id}"]`)
}


function Create(tableBody, payload){
    const row = tableBody.insertRow()
    row.dataset.id = payload.id
    row.innerHTML = `
    <td class="id">${payload.id}</td>
    <td class="label">${payload.label}</td>
    `
}

function Delete(tableBody,payload){
    const item = Find(tableBody,payload.id)
    if ( item ){ item.remove() }
}

function Update(tableBody,payload){
    const item = Find(tableBody,payload.id)
    if (! item){
        console.warn(`Failure to find item to update: ... ${tableBody} \n ... ${payload.id}`)
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