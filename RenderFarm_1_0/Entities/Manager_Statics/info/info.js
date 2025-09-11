var ws = new WebSocket(`ws://${window.location.host}/state-info`);
ws.onmessage = function(event) {
    var message = JSON.parse(event.data)
    const {command, catagory,  payload} = message

    var container = document.getElementById(catagory)

    var template  = document.getElementById(`${catagory}-lineitem-template`)
    if (template == null){
        var template = document.getElementById('generic-lineitem-template')
    }

    switch (command){
        case "CREATE":{
            const new_item = Create(catagory,container,template,payload)
            Update(catagory, new_item, payload)
            break
        }

        case "UPDATE":{
            var item = container.getElementById(payload.id)
            if (! item){
                console.warn(`Failure to find item to update: ${command} \n ... ${container} \n ... ${payload.id}`)
            } // TODO: Request when missing from websocket
            Update(catagory, item, payload)            
        }

        case "DELETE":{
            Delete(catagory,container,template,payload)
            break
        }

        case "CLEAR":{
            Clear(catagory,container,payload)
            break
        }

        default:{
            console.warn(`Failure to parse command: ${command} \n ... ${catagory} \n ... ${payload}`)
        }
    }
};

function Create(catagory,container,template,payload){
    // Create, re-create as required

    Delete(catagory,container,payload.id)

    const new_item = template.content.cloneNode(True)
    new_item.id    = payload.id
    return new_item
}

function Delete(catagory,container,id){
    const item = container.getElementById(id)
    if (item){listItem.remove()}
}

function Update(catagory,new_item,payload){
    Object.entries(payload).forEach(([key,value]) => {
        if (new_item[key]){new_item[key].value = value}
        else {console.warn(`Failure to Find key: ${catagory} \n ... ${new_item.id} \n ... ${key}.value : ${value}`)}
    });
}

function Clear(catagory,container,payload){
    container.children.forEach((child) => {
        container.children.remove(child)
    })
}
    



// function sendMessage(event) {
//     var input = document.getElementById("messageText")
//     ws.send(input.value)
//     input.value = ''
//     event.preventDefault()
// };