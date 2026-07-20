#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; Global variables
isRunning := false
delay := 0
extraTabs := 0
dataLines := []
currentIndex := 1

; F4 to toggle the script on/off
F4:: {
    global isRunning, currentIndex
    
    if (isRunning) {
        ; Stop the script
        isRunning := false
        ToolTip "AutoEntry Stopped"
        SetTimer () => ToolTip(), -2000
        return
    }
    
    ; Start the script
    if (ReadDataFile()) {
        isRunning := true
        ToolTip "AutoEntry Started"
        SetTimer () => ToolTip(), -2000
        currentIndex := 1
        SetTimer ProcessNextValue, -1
    }
}

; Escape to stop the script
Esc:: {
    global isRunning
    
    if (isRunning) {
        isRunning := false
        ToolTip "AutoEntry Stopped"
        SetTimer () => ToolTip(), -2000
    }
}

; Read the data file
ReadDataFile() {
    global delay, extraTabs, dataLines
    
    ; Clear previous data
    dataLines := []
    
    ; Check if file exists
    if (!FileExist("parsed_data.txt")) {
        MsgBox "Error: parsed_data.txt file not found!"
        return false
    }
    
    ; Read the file
    try {
        fileContent := FileRead("parsed_data.txt")
    } catch {
        MsgBox "Error: Could not read parsed_data.txt!"
        return false
    }
    
    ; Split into lines and remove empty ones
    lines := StrSplit(fileContent, "`n", "`r")
    
    ; Check if file has at least 2 lines (speed and tabs)
    if (lines.Length < 2) {
        MsgBox "Error: File is missing required data!"
        return false
    }
    
    ; Get speed and extra tabs from first two lines
    delay := Integer(Trim(lines[1]))
    extraTabs := Integer(Trim(lines[2]))
    
    ; Store remaining lines as data
    Loop lines.Length - 2 {
        value := Trim(lines[A_Index + 2])
        if (value != "") {
            dataLines.Push(value)
        }
    }
    
    ; Check if we have data
    if (dataLines.Length = 0) {
        MsgBox "Error: No data to process!"
        return false
    }
    
    return true
}

; Process the next value in the sequence
ProcessNextValue() {
    global isRunning, delay, extraTabs, dataLines, currentIndex
    
    ; Check if we should stop
    if (!isRunning) {
        return
    }
    
    ; Check if we're done
    if (currentIndex > dataLines.Length) {
        isRunning := false
        return
    }
    
    ; Get current value
    value := dataLines[currentIndex]
    
    ; Determine what to do based on position in the 4-value cycle
    position := Mod(currentIndex - 1, 4) + 1
    
    ; Type the value
    SendText value
    Sleep delay
    
    ; Handle tabs and enter based on position
    if (position = 1) {
        ; After 1st value: Tab
        Send "{Tab}"
        Sleep delay
    }
    else if (position = 2) {
        ; After 2nd value: Tab
        Send "{Tab}"
        Sleep delay
    }
    else if (position = 3) {
        ; After 3rd value: Tab, then extra tabs
        Send "{Tab}"
        Sleep delay
        
        Loop extraTabs {
            Send "{Tab}"
            Sleep delay
        }
    }
	else if (position = 4) {
			; After 4th value: check if this is the LAST item
			if (currentIndex < dataLines.Length) {
				; Not the last item - do Tab, Tab, Enter
				Send "{Tab}"
				Sleep delay
				
				Send "{Tab}"
				Sleep delay
				
				Send "{Enter}"
				Sleep delay
			}
			; If it IS the last item, don't send any keystrokes after paste
		}
    
    ; Move to next value
    currentIndex++
    
    ; Schedule next value
    SetTimer ProcessNextValue, -1
    return
}