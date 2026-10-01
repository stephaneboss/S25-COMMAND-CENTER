# Dell Windows UI bridge

`tools/windows_ui_bridge.ps1` runs in the signed-in Windows desktop session.
It uses Windows UI Automation to list windows, GDI for a screenshot, and
Win32 input to click and type. It opens no listener or firewall port.
Run it with Windows PowerShell under the interactive user `Steph`.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\windows_ui_bridge.ps1 -Action windows
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\windows_ui_bridge.ps1 -Action screenshot
```

Read the returned screenshot from the temporary path, then delete it.
Window listings include a PID and a window handle. For Chrome or VS Code,
supply **both** because one process can own several windows.
After visually locating an element, use coordinates inside the intended
window. A click refuses a mismatched handle, a covered coordinate, or a
coordinate outside the target rectangle. It confirms the target is focused.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\windows_ui_bridge.ps1 -Action click -TargetPid 1234 -TargetHandle 5678 -X 400 -Y 250
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\windows_ui_bridge.ps1 -Action type -TargetPid 1234 -TargetHandle 5678 -Text 'Test'
```

For private or long text, use `-TextFile` with a local private file
instead of putting its contents in the process command line. The bridge
checks the foreground window before every character and stops on focus loss.
Verify the result with a new screenshot before another action.
The session must be interactive and unlocked. Elevated windows and
Windows' secure desktop are outside this bridge's scope. The script
does not make a completed task, sent email, or deployed change true;
verify each result in the target application and keep mission receipts.

Smoke test on the Dell: a temporary Notepad window was focused by
a targeted click, Unicode text was typed, and a screenshot showed
the exact text. The temporary window and screenshots were removed.
Invalid handles and out-of-window clicks returned errors.
No business application was edited during this test.
