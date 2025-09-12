var ws = new WebSocket(`ws://${window.location.host}/state-info`);
ws.onmessage = function(event) {
    // console.warn(event.data)
    var message = JSON.parse(event.data)
    // const {command, catagory,  payload} = message
    const command = message[0]
    const catagory = message[1]
    const payload = message[2]

    var container = document.getElementById(catagory)

    var template  = document.getElementById(`${catagory}-lineitem-template`)
    if (template == null){
        var template = document.getElementById('generic-lineitem-template')
    }

    switch (command){
        case "BULK_CREATE":{
            payload.forEach((payload_item) =>{
                // console.warn(payload_item)
                Create(catagory,container,template,payload_item)
                // const new_item = Create(catagory,container,template,payload_item)
                // Update(catagory, new_item, payload_item)}
            })
            break
        }
        case "CREATE":{
            const new_item = Create(catagory,container,template,payload)
            // Update(catagory, new_item, payload)
            break
        }

        case "UPDATE":{
            const item = document.getElementById(`${catagory}-${payload.id}`)
            if (! item){
                console.warn(`Failure to find item to update: ... ${container} \n ... ${payload.id}`)
            }
            else {Update(catagory, item, payload)}            
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


function Create(catagory,container,template, payload){
    // Create, re-create as required

    Delete(catagory,container,payload.id)

    // const new_item = template.content.cloneNode(true)
    const new_item = template.content.structuredClone(true)
    new_item.id    = `${catagory}-${payload.id}`
    
    Update(catagory, new_item, payload)
    container.appendChild(new_item)

    return new_item
}

function Delete(catagory,container,id){
    const item = document.getElementById(`${catagory}-${id}`)
    // const item = container.getElementById(id)
    if (item){listItem.remove()}
}

function Update(catagory,item,payload){
    // console.warn('ITEM:',item)
    item.querySelector('.label').textContent = payload.label
    
    // column_template = document.getElementById('lineitem-column-template')
    // value_list = item.quirySelector('.values')
    // Object.entries(payload).forEach(([key,value]) => {
    //     column_item = value_list.quirySelector(`.${key}`
    //     if (column_item)){
            
    //     }else{

    //     }
    // });

    
    Object.entries(payload).forEach(([key,value]) => {
        // console.warn(`${payload} | ${key} : ${value} `) 
        item.querySelector(`.${key}`).textContent = value
        node = item.querySelector(`.${key}`)
        if (node){node.textContent  = value}
        else {console.warn(`Failure to find key: ${item.id} |  ${key} : ${value} \n  ${node}    `)}
        });

    // console.warn(`End_Update `)
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