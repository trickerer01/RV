########################
#
# 1) rv

$RUN_PYTHON3 = "python.exe"  # has to be in PATH
$TimeFormat = "HH:mm:ss"

$MYWORKDIR = "./"
$SCRIPT_PATH = "ids.py"

$par1 = New-Object System.Collections.ArrayList

$par1.Add($SCRIPT_PATH) > $null
$par1.Add($MYWORKDIR) > $null

$startTime = Get-Date -Format $TimeFormat

$start_id = [Int32]($args[0])
$count = [Int32]($args[1])
$quality_str = $args[2]

if ($start_id -lt 1 -or $start_id -gt 4000000)
{ write("Invalid syntax!"); return }
if ($count -eq $null -or $count -eq 0)
{ $count = 1 }
if ($count -lt 1 -or $count -gt 4000000)
{ write("Invalid syntax!"); return }
if ($quality_str -eq $null)
{ $quality_str = "'default'" }

$par1.Add($start_id) > $null
$par1.Add($start_id + $count - 1) > $null
$par1.Add($quality_str) > $null

write("processing ids " + $start_id + "-" + ($start_id + $count - 1) + " (quality: " + $quality_str + ")...")

(&"$RUN_PYTHON3" $par1)

$endTime = Get-Date -Format $TimeFormat
$timestr = "Started at " + $startTime + ", ended at " + $endTime
write $timestr

#
########################
