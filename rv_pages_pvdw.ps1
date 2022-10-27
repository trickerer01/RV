########################
#
# 1) rv

$RUN_PYTHON3 = "python.exe"  # has to be in PATH
$SYNTAX_ = "Syntax: #start_page #num_pages [#do_full=0,1,2] [#stop_id] [#search_string] [#proxy]"
$TimeFormat = "HH:mm:ss"

$MYWORKDIR = "./"
$SCRIPT_PATH = "src/pages.py"

$par1 = New-Object System.Collections.ArrayList

$par1.Add($SCRIPT_PATH) > $null
$par1.Add("-path") > $null
$par1.Add($MYWORKDIR) > $null

$startTime = Get-Date -Format $TimeFormat

$start_page = [Int32]($args[0])
$num_pages = [Int32]($args[1])
$do_full = [Int32]($args[2])
$stop_id = [Int32]($args[3])
$search_str = [String]($args[4])
$proxy = [String]($args[5])

if ($start_page -lt 1 -or $start_page -gt 100000)
{ write($SYNTAX_); return }
if ($num_pages -eq $null -or $num_pages -eq 0)
{ $num_pages = 1 }
if ($num_pages -lt 1 -or $num_pages -gt 1000)
{ write($SYNTAX_); return }
if ($do_full -ne 0 -and $do_full -ne 1 -and $do_full -ne 2)
{ write($SYNTAX_); return }

$par1.Add($start_page) > $null
$par1.Add($num_pages) > $null
$par1.Add($do_full) > $null
if ($stop_id -gt 0)
{ $par1.Add($stop_id) > $null }
if ($search_str -ne $null)
{ $par1.Add($search_str) > $null }
if ($proxy -ne "")
{
    $par1.Add("-proxy") > $null
    $par1.Add($proxy) > $null
}

write("processing pages " + $start_page + "-" + ($start_page + $num_pages - 1) + "...")

(&"$RUN_PYTHON3" $par1)

$endTime = Get-Date -Format $TimeFormat
$timestr = "Started at " + $startTime + ", ended at " + $endTime
write $timestr

#
########################
