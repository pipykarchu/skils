# scan-workspace.ps1 — 工作区深度扫描统计脚本（Windows PowerShell 5.1 兼容）
# 用法: powershell -ExecutionPolicy Bypass -File scan-workspace.ps1 -Root "D:\AI\AI产品工作"
# 输出: 顶层结构 / 文件总数 / 扩展名分布 TOP20 / 按顶层目录分布 / 目录体积排序（找冗余）
# 注意: 管道尾 Format-Table/Select-Object 会导致 $LASTEXITCODE=1，这是误报，输出正常。

param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string[]]$Exclude = @('_remote-audit','_worktrees','_migration-quarantine','_archive',
                           'node_modules','backup','.git','.global-model-runtime','_同名不同版本','.tmp')
)

if (-not (Test-Path $Root)) { Write-Error "路径不存在: $Root"; exit 2 }

function Test-Excluded([string]$fullPath) {
    foreach ($e in $Exclude) {
        if ($fullPath -match "\\$([regex]::Escape($e))(\\)?$") { return $true }
        # 目录自身或其路径段匹配
        if ($fullPath -match "\\$([regex]::Escape($e))(\\|$)") { return $true }
    }
    return $false
}

Write-Host "=== 1. 顶层目录 ==="
Get-ChildItem -Path $Root -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { -not (Test-Excluded $_.FullName) } |
    ForEach-Object { $s = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
                          Measure-Object -Property Length -Sum).Sum;
                     "{0}  |  {1} MB" -f $_.Name, [math]::Round($s/1MB,1) }

Write-Host ""
Write-Host "=== 2. 文件总数（排除后）==="
$files = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
         Where-Object { -not (Test-Excluded $_.FullName) }
Write-Host ("总文件数: {0}" -f $files.Count)

Write-Host ""
Write-Host "=== 3. 扩展名分布 TOP20 ==="
$files | Group-Object Extension | Sort-Object Count -Descending |
    Select-Object -First 20 Name, Count | Format-Table -AutoSize

Write-Host "=== 4. 按顶层目录分布 ==="
$files | Group-Object { ($_.FullName -replace [regex]::Escape($Root + '\'), '').Split('\')[0] } |
    Sort-Object Count -Descending |
    ForEach-Object { "{0}: {1} 文件" -f $_.Name, $_.Count }

Write-Host ""
Write-Host "=== 5. 目录体积排序（找冗余）==="
Get-ChildItem -Path $Root -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { -not (Test-Excluded $_.FullName) } |
    ForEach-Object { $s = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue |
                          Measure-Object -Property Length -Sum).Sum;
                     [PSCustomObject]@{ Dir = $_.Name; MB = [math]::Round($s/1MB,0) } } |
    Sort-Object MB -Descending |
    ForEach-Object { "{0}: {1} MB" -f $_.Dir, $_.MB }

Write-Host ""
Write-Host "=== 6. 指定扩展名分布（如 html 原型）==="
$files | Where-Object { $_.Extension -eq '.html' } |
    Group-Object { ($_.FullName -replace [regex]::Escape($Root + '\'), '').Split('\')[0] } |
    ForEach-Object { "{0}: {1} html" -f $_.Name, $_.Count }

Write-Host "扫描完成。注意：exit_code=1 通常是管道尾 Format-Table 误报，忽略。"
