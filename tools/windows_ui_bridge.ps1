# Interactive Windows UI bridge. Run as the signed-in user; no network listener.
param(
    [ValidateSet('windows','screenshot','click','type')][string]$Action = 'windows',
    [int]$TargetPid = 0,
    [long]$TargetHandle = 0,
    [int]$X = -1,
    [int]$Y = -1,
    [string]$Text = '',
    [string]$TextFile = '',
    [string]$OutputPath = ''
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class S25Input {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT {
        public ushort Vk, Scan; public uint Flags, Time; public IntPtr Extra;
    }
    [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT {
        public int X, Y; public uint Data, Flags, Time; public IntPtr Extra;
    }
    [StructLayout(LayoutKind.Explicit)] public struct UNION {
        [FieldOffset(0)] public KEYBDINPUT Keyboard;
        [FieldOffset(0)] public MOUSEINPUT Mouse;
    }
    [StructLayout(LayoutKind.Sequential)] public struct INPUT {
        public uint Type; public UNION Data;
    }
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(
        IntPtr h, IntPtr after, int x, int y, int width, int height, uint flags);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
    [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint flags);
    [DllImport("user32.dll")] public static extern void mouse_event(
        uint flags, uint x, uint y, uint data, UIntPtr extra);
    [DllImport("user32.dll", SetLastError=true)] static extern uint SendInput(
        uint count, INPUT[] input, int size);
    public static void TypeUnicode(string value, IntPtr target) {
        foreach (char c in value) {
            if (GetAncestor(GetForegroundWindow(), 2) != target)
                throw new InvalidOperationException("Target lost foreground; typing stopped");
            INPUT down = new INPUT { Type=1, Data=new UNION {
                Keyboard=new KEYBDINPUT { Scan=c, Flags=4 } } };
            INPUT up = new INPUT { Type=1, Data=new UNION {
                Keyboard=new KEYBDINPUT { Scan=c, Flags=6 } } };
            if (SendInput(2, new INPUT[] { down, up },
                Marshal.SizeOf(typeof(INPUT))) != 2)
                throw new System.ComponentModel.Win32Exception(
                    Marshal.GetLastWin32Error(), "Keyboard input was blocked");
        }
    }
}
'@
function ForegroundPid {
    [uint32]$owner = 0
    [void][S25Input]::GetWindowThreadProcessId(
        [S25Input]::GetForegroundWindow(), [ref]$owner)
    return [int]$owner
}
if ($Action -eq 'windows') {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition)
    $result = @(foreach ($win in $wins) {
        if ($win.Current.Name) {
            [pscustomobject]@{Name=$win.Current.Name;Pid=$win.Current.ProcessId;
                Handle=$win.Current.NativeWindowHandle}
        }
    })
    $result | ConvertTo-Json -Compress
    return
}
if ($Action -eq 'screenshot') {
    if (-not $OutputPath) {
        $OutputPath = Join-Path $env:TEMP 's25-ui-screenshot.png'
    }
    $rect = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap($rect.Width, $rect.Height)
    $gfx = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $gfx.CopyFromScreen($rect.Location, [System.Drawing.Point]::Empty, $rect.Size)
        $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        [pscustomobject]@{Path=$OutputPath;Width=$rect.Width;Height=$rect.Height} |
            ConvertTo-Json -Compress
    } finally { $gfx.Dispose(); $bitmap.Dispose() }
    return
}
if ($TargetPid -le 0) { throw 'TargetPid is required for click and type' }
$process = Get-Process -Id $TargetPid -ErrorAction Stop
$handle = if ($TargetHandle) { [IntPtr]$TargetHandle } else {
    [IntPtr]$process.MainWindowHandle
}
if ($handle -eq [IntPtr]::Zero) { throw 'Target has no window' }
[uint32]$windowOwner = 0
[void][S25Input]::GetWindowThreadProcessId($handle,[ref]$windowOwner)
if ($windowOwner -ne $TargetPid) { throw 'Target handle does not belong to PID' }
if ($Action -eq 'type') {
    if ($TextFile -and $Text) { throw 'Choose Text or TextFile' }
    if ($TextFile) { $Text = [System.IO.File]::ReadAllText($TextFile) }
    if (-not $Text -or $Text.Length -gt 4000) {
        throw 'Text must contain 1 to 4000 characters'
    }
    if ([S25Input]::GetAncestor([S25Input]::GetForegroundWindow(),2) -ne $handle) {
        throw 'Target lost foreground; no text was sent'
    }
    [S25Input]::TypeUnicode($Text,$handle)
    [pscustomobject]@{Action='type';Pid=$TargetPid;Handle=$handle.ToInt64();
        Characters=$Text.Length;ForegroundConfirmed=$true} | ConvertTo-Json -Compress
    return
}
if ($X -lt 0 -or $Y -lt 0) { throw 'X and Y are required for click' }
$rect = New-Object S25Input+RECT
if (-not [S25Input]::GetWindowRect($handle, [ref]$rect)) {
    throw 'Cannot read target bounds'
}
if ($X -lt $rect.Left -or $X -ge $rect.Right -or
    $Y -lt $rect.Top -or $Y -ge $rect.Bottom) {
    throw 'Click is outside target window'
}
$wasForeground = ((ForegroundPid) -eq $TargetPid)
try {
    if (-not $wasForeground) {
        if (-not [S25Input]::SetWindowPos($handle, [IntPtr](-1),0,0,0,0,3)) {
            throw 'Could not bring target window above other windows'
        }
        Start-Sleep -Milliseconds 150
    }
    $point = New-Object S25Input+POINT
    $point.X = $X; $point.Y = $Y
    $atPoint = [S25Input]::GetAncestor(
        [S25Input]::WindowFromPoint($point), 2)
    if ($atPoint -ne $handle) {
        throw 'Another window covers the click point'
    }
    [void][S25Input]::SetCursorPos($X,$Y)
    [S25Input]::mouse_event(2,0,0,0,[UIntPtr]::Zero)
    [S25Input]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
    Start-Sleep -Milliseconds 150
    if ([S25Input]::GetAncestor([S25Input]::GetForegroundWindow(),2) -ne $handle) {
        throw 'Click did not focus the target window'
    }
    [pscustomobject]@{Action='click';Pid=$TargetPid;Handle=$handle.ToInt64();
        X=$X;Y=$Y;ForegroundConfirmed=$true} | ConvertTo-Json -Compress
} finally {
    if (-not $wasForeground) {
        [void][S25Input]::SetWindowPos($handle, [IntPtr](-2),0,0,0,0,3)
    }
}
