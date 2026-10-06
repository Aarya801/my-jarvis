$port = 8765
$ErrorActionPreference = "Stop"
$tokFile = "$env:USERPROFILE\.jarvis_bridge_token"
if (!(Test-Path $tokFile)) {
  $t = -join ((1..32 | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) }))
  [System.IO.File]::WriteAllText($tokFile, $t)
}
$TOKEN = [System.IO.File]::ReadAllText($tokFile).Trim()
$listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $port)
try { $listener.Start() } catch { Write-Host "START FAILED: $_"; pause; exit 1 }
Write-Host "JARVIS bridge listening on http://127.0.0.1:$port"
Write-Host "TOKEN (paste into JARVIS if asked): $TOKEN"
Write-Host "Keep this window open. Closing it stops direct PC access."
function Send-Res($stream, $body, $code=200, $ctype="text/plain; charset=utf-8") {
  $b = [Text.Encoding]::UTF8.GetBytes($body)
  $reason = "OK"
  if ($code -eq 400) { $reason = "Bad Request" } elseif ($code -eq 403) { $reason = "Forbidden" } elseif ($code -eq 404) { $reason = "Not Found" } elseif ($code -eq 500) { $reason = "Error" }
  $crlf = [char]13 + [char]10
  $h = "HTTP/1.1 $code $reason" + $crlf + "Content-Type: $ctype" + $crlf + "Content-Length: $($b.Length)" + $crlf + "Cache-Control: no-store" + $crlf + "Access-Control-Allow-Origin: https://perchance.org" + $crlf + "Access-Control-Allow-Headers: X-Token, Content-Type" + $crlf + "Access-Control-Allow-Private-Network: true" + $crlf + "Access-Control-Allow-Methods: GET, POST, OPTIONS" + $crlf + "Connection: close" + $crlf + $crlf
  $hb = [Text.Encoding]::ASCII.GetBytes($h)
  $stream.Write($hb,0,$hb.Length); $stream.Write($b,0,$b.Length); $stream.Flush()
}
while ($true) {
  $client = $listener.AcceptTcpClient()
  try {
    $stream = $client.GetStream()
    $reader = New-Object System.IO.StreamReader($stream, [Text.Encoding]::UTF8)
    $reqLine = $reader.ReadLine()
    if (!$reqLine) { $client.Close(); continue }
    $parts = $reqLine -split " "
    $method = $parts[0]; $raw = $parts[1]
    $headers = @{}
    while ($true) {
      $line = $reader.ReadLine()
      if ($null -eq $line -or $line -eq "") { break }
      $i = $line.IndexOf(":")
      if ($i -gt 0) { $headers[$line.Substring(0,$i).Trim().ToLower()] = $line.Substring($i+1).Trim() }
    }
    $len = 0
    if ($headers.ContainsKey("content-length")) { [void][int]::TryParse($headers["content-length"], [ref]$len) }
    $body = ""
    if ($len -gt 0 -and $len -lt 2000000) {
      $buf = New-Object char[] $len; $got = 0
      while ($got -lt $len) { $n = $reader.Read($buf,$got,$len-$got); if ($n -le 0) { break }; $got += $n }
      if ($got -gt 0) { $body = -join $buf[0..($got-1)] }
    }
    $qi = $raw.IndexOf("?")
    if ($qi -ge 0) { $apath = $raw.Substring(0,$qi); $qs = $raw.Substring($qi+1) } else { $apath = $raw; $qs = "" }
    $qp = @{}
    foreach ($item in $qs -split "&") { if ($item -ne "") { $e=$item.IndexOf("="); if ($e -ge 0) { $qp[$item.Substring(0,$e)] = [System.Uri]::UnescapeDataString($item.Substring($e+1)) } } }
    if ($method -eq "OPTIONS") { Send-Res $stream "" 200; $client.Close(); continue }
    if ($apath -eq "/status") { Send-Res $stream '{"ok":true,"service":"jarvis-bridge","scope":"loopback"}' 200 "application/json"; $client.Close(); continue }
    if ($headers["x-token"] -ne $TOKEN) { Send-Res $stream "bad token" 403; $client.Close(); continue }
    try {
      if ($apath -eq "/ls") {
        $d=$qp["path"]; if (!$d) {$d="$env:USERPROFILE\Desktop"}; $d=[Environment]::ExpandEnvironmentVariables($d).Replace("~",$env:USERPROFILE)
        $fs=Get-ChildItem -LiteralPath $d | Select-Object -First 200 | ForEach-Object {'{"name":'+($_.Name|ConvertTo-Json -Compress)+',"dir":'+$_.PSIsContainer.ToString().ToLower()+'}'}
        Send-Res $stream ('{"path":'+($d|ConvertTo-Json -Compress)+',"files":['+($fs -join ",")+']}') 200 "application/json"
      } elseif ($apath -eq "/read") {
        $f=[Environment]::ExpandEnvironmentVariables($qp["path"]).Replace("~",$env:USERPROFILE); Send-Res $stream ([System.IO.File]::ReadAllText($f))
      } elseif ($apath -eq "/run") {
        $cmd=""; try {$cmd=(ConvertFrom-Json $body).cmd} catch {$cmd=$body}
        if ([string]::IsNullOrWhiteSpace($cmd)) {Send-Res $stream "missing command" 400; $client.Close(); continue}
        $p=New-Object System.Diagnostics.Process; $p.StartInfo.FileName="cmd.exe"; $p.StartInfo.Arguments="/c "+$cmd; $p.StartInfo.RedirectStandardOutput=$true; $p.StartInfo.RedirectStandardError=$true; $p.StartInfo.UseShellExecute=$false; $p.StartInfo.CreateNoWindow=$true; $p.Start()|Out-Null
        if (!$p.WaitForExit(30000)) {try {$p.Kill()} catch {}; Send-Res $stream "timed out after 30s" 500} else {$o=$p.StandardOutput.ReadToEnd()+$p.StandardError.ReadToEnd(); if (!$o) {$o="(no output)"}; if ($o.Length -gt 20000) {$o=$o.Substring(0,20000)}; Send-Res $stream $o}
      } elseif ($apath -eq "/write") {
        $o=ConvertFrom-Json $body; $fp=[Environment]::ExpandEnvironmentVariables($o.path).Replace("~",$env:USERPROFILE); New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($fp))|Out-Null; [System.IO.File]::WriteAllText($fp,$o.content); Send-Res $stream ("saved "+$fp)
      } else {Send-Res $stream "not found" 404}
    } catch {Send-Res $stream $_.Exception.Message 500}
    $client.Close()
  } catch {try {$client.Close()} catch {}}
}