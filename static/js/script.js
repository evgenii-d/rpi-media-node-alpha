const infoWrapper = document.getElementById('info')
const machineControlWrapper = document.getElementById('machine-control')

const playerControlWrapper = document.getElementById('player-control')
const volumeControl = playerControlWrapper.querySelector('[data-cmd=volume]')
const videoNumber = playerControlWrapper.querySelector('[placeholder="video #"]')

const playerSettingsWrapper = document.getElementById('player-settings')

const uploadWrapper = document.getElementById('upload-wrapper')
const mediaFiles = document.querySelector('#upload-wrapper input')
const submitMediaBtn = document.querySelector('#upload-wrapper button')

const mediaListWrapper = document.getElementById('media-list')
const usedSpaceLabel = document.querySelector('#media-list [data-id=used-space]')
const mediaList = document.querySelector('#media-list>table>tbody')

let formData

function removeChildElements(parent) { while (parent.firstChild) { parent.removeChild(parent.firstChild) } }

function getUsedSpace() {
    fetch('/info/used-space').then(r => r.text())
        .then(v => { usedSpaceLabel.textContent = Math.round(v) })
}

function handleFiles(e) {
    const text = e.currentTarget.parentNode.querySelector('span')
    const files = e.currentTarget.files

    formData = new FormData()
    for (let i = 0; i < files.length; i++) formData.append('media', files[i])

    if (files.length > 1)
        text.textContent = `${files.length} files selected`
    else
        text.textContent = `${files[0].name}`
}

function updatePlaylistOrder() {
    const checkboxes = mediaList.querySelectorAll('input')
    const list = []
    let numbers
    checkboxes.forEach(checkbox => { list.push(checkbox.value) })

    mediaListWrapper.disabled = true
    fetch('/playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(list)
    }).then(response => {
        response.text().then(text => {
            if (response.status == 200) {
                console.info(text)
                numbers = mediaList.querySelectorAll('[data-number]')
                numbers.forEach((number, i) => { number.textContent = i + 1 })
            } else console.error('Something wrong with playlist order')

            mediaListWrapper.disabled = false
        })
    })
}

function orderHandler(e) {
    const element = e.target
    if (element.type !== 'submit') { return }

    const prevNode = element.parentNode.parentNode.previousElementSibling
    const nextNode = element.parentNode.parentNode.nextElementSibling
    const currentNode = element.parentNode.parentNode

    if (element.hasAttribute('data-prev') && prevNode)
        mediaList.insertBefore(currentNode, prevNode)

    if (element.hasAttribute('data-next') && nextNode)
        mediaList.insertBefore(nextNode, currentNode)
}

function getPlaylist() {
    fetch('/playlist')
        .then(response => response.json())
        .then(data => {
            removeChildElements(mediaList)

            if (data.playlist.length === 0) {
                mediaListWrapper.dataset.empty = true
                return
            }

            mediaListWrapper.dataset.empty = false
            data.playlist.forEach((element, i) => {
                const tr = `
                    <tr>
                        <td><input type=checkbox value="${element}"></td>
                        <td><a href="static/media/${element}" download>${element}</a></td>
                        <td data-number>${i + 1}</td>
                        <td data-order>
                            <button data-prev></button>
                            <button data-next></button>
                        </td>
                    </tr>
                `
                mediaList.insertAdjacentHTML('beforeend', tr)
                mediaList.lastElementChild.querySelector('[data-order]')
                    .addEventListener('click', orderHandler)
            })
        })
}

function uploadMedia() {
    if (mediaFiles.files.length === 0) { alert('Select files'); return }

    uploadWrapper.disabled = true
    fetch('/media', { method: 'POST', body: formData })
        .then(response => {
            response.text().then(text => {
                if (response.status == 201) console.info(text)
                else console.error('Something wrong with upload')

                uploadWrapper.disabled = false
                getPlaylist()
                getUsedSpace()
            })
        })
}

function deleteMedia() {
    const checkboxes = mediaList.querySelectorAll('input:checked')
    const list = []

    checkboxes.forEach(checkbox => { checkbox.value ? list.push(checkbox.value) : '' })
    if (list.length === 0) { alert('Choose files'); return }

    if (confirm('Are you sure?')) {
        mediaListWrapper.disabled = true
        fetch('/media', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(list)
        }).then(response => {
            if (response.status == 200) {
                getPlaylist()
                getUsedSpace()
                console.info('delete done')
            } else console.error('Something wrong with files to delete')
            mediaListWrapper.disabled = false
        })
    }
}

function playerControlHandler(e) {
    const wrapper = e.currentTarget
    const element = e.target
    const command = element.dataset.cmd
    const resource = { url: null, init: null }

    if (!command) return

    switch (element.type) {
        case 'submit':
            resource.url = `/playlist?command=${command}`
            resource.init = { method: 'GET' }

            if (command === 'goto') {
                if (videoNumber.value === '') { return }
                resource.url = `/playlist?command=${command}&value=${videoNumber.value}`
            }
            break
        case 'range':
            resource.url = `/player-settings/volume?value=${element.value}`
            resource.init = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ value: +element.value })
            }
            break
    }

    wrapper.disabled = true
    fetch(resource.url, resource.init)
        .then(response => {
            response.text().then(text => { console.info(text); wrapper.disabled = false })
        })
}

function playerSettingsHandler(e) {
    const wrapper = e.currentTarget
    const element = e.target
    const parent = element.tagName === 'INPUT' ? element.parentNode.parentNode : element.parentNode
    const settings = parent.dataset.settings
    let resource = { url: null, value: null }

    wrapper.disabled = true
    switch (settings) {
        case 'modules':
            resource = {
                url: '/player-settings/module',
                value: JSON.stringify({ value: element.value })
            }
            break
        case 'options':
            const checkboxes = parent.querySelectorAll('[type=checkbox]')
            const list = []

            checkboxes.forEach(box => { box.checked ? list.push(box.value) : '' })
            resource = {
                url: '/player-settings/options',
                value: JSON.stringify({ value: list })
            }
            break
        case 'remote-nodes':
            const addresses = element.value.split(/\r\n|\r|\n/).filter(a => a !== '')

            addresses.forEach((a, i) => { addresses[i] = a.trim() })
            element.value = addresses.join(' ')

            resource = {
                url: '/player-settings/remote-nodes',
                value: JSON.stringify({ value: addresses })
            }
            break
    }

    fetch(resource.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: resource.value
    })
        .then(response => response.text())
        .then(text => { console.info(text); wrapper.disabled = false })
}

function infoHandler(e) {
    const element = e.target
    const newName = element.value

    element.disabled = true
    switch (element.type) {
        case 'text':
            fetch('/info/name', { method: 'POST', body: newName })
                .then(response => {
                    response.text().then(string => {
                        if (response.status == 200) {
                            console.info(string)
                        } else {
                            element.value = string
                            alert('Error: maximum length exceeded')
                        }
                        element.disabled = false
                    })
                })
            break
    }
}

function machineControlHandler(e) {
    const wrapper = e.currentTarget
    const command = e.target.dataset.cmd

    if (command) {
        if (confirm(`${command.toUpperCase()} will be executed. Are you sure?`)) {
            wrapper.disabled = true
            fetch(`/machine-control/${command}`)
                .then(response => response.text())
                .then(text => { console.info(text); wrapper.disabled = false })
        }
    }
}

function mediaListHandler(e) {
    switch (e.target.dataset.id) {
        case 'select-all':
            const controlCheckbox = e.target
            const checkboxes = mediaList.querySelectorAll('input')
            checkboxes.forEach(checkbox => checkbox.checked = controlCheckbox.checked)
            break
        case 'delete':
            deleteMedia()
            break
        case 'update':
            updatePlaylistOrder()
            break
    }
}

function videoNumberHandler(e) {
    switch (e.type) {
        case 'click':
            e.target.value = ''
            break
        case 'input':
            e.target.value = e.target.value.replace(/[^0-9]/g, '')
            break
    }
}

infoWrapper.addEventListener('change', infoHandler)
machineControlWrapper.addEventListener('click', machineControlHandler)

playerControlWrapper.addEventListener('click', playerControlHandler)
playerControlWrapper.addEventListener('change', playerControlHandler)
playerSettingsWrapper.addEventListener('change', playerSettingsHandler)
videoNumber.addEventListener('click', videoNumberHandler)
videoNumber.addEventListener('input', videoNumberHandler)

mediaListWrapper.addEventListener('click', mediaListHandler)
mediaFiles.addEventListener('change', handleFiles)
submitMediaBtn.addEventListener('click', uploadMedia)

getPlaylist()