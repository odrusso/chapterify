import {useEffect, useState} from "react";

const {ipcRenderer} = require('electron');

export const App = () => {
    const [fileLocation, setFileLocation] = useState<string | null>(null)
    const [saveLocation, setSaveLocation] = useState<string | null>(null)
    const [progress, setProgress] = useState<string | null>(null)

    // Run once setup listeners
    useEffect(() => {
        ipcRenderer.on('file', (event, file) => {
            setFileLocation(file)
        });

        ipcRenderer.on('save-file', (event, file) => {
            setSaveLocation(file)
        });

        ipcRenderer.on('progress', (event, update) => {
            setProgress(update)
        });
    })

    const getFileLocation = async () => {
        ipcRenderer.send('file-request')
    }

    const getSaveLocation = async () => {
        ipcRenderer.send('save-file-request')
    }

    const merge = async () => {
        ipcRenderer.send('merge', {fileLocation: fileLocation, saveLocation: saveLocation})
    }

    return (
        <>
            <center>
                <h1>Chapterify</h1>
                <button onClick={getFileLocation}>Select folder containing mp3 files</button>
                <p>{fileLocation}</p>
                <button onClick={getSaveLocation}>Select save m4b file destination</button>
                <p>{saveLocation}</p>
                <button onClick={merge}>Merge</button>
                <br />
                <h2>{progress}</h2>
            </center>
        </>
    )
}
