# 一键拉取开源运维知识库语料
#
# 用途:
#   - 克隆精选的开源 SRE / On-Call / Incident Response markdown 仓库
#   - 抽取所有 .md 文件到 data/kb_corpus/<repo_name>/
#   - 跳过 LICENSE / CONTRIBUTING 等无关文档
#   - 输出统计: 共拉取多少文件、多少字
#
# 用法:
#   pwsh scripts/fetch_kb_corpus.ps1
#   或
#   powershell.exe -ExecutionPolicy Bypass -File scripts/fetch_kb_corpus.ps1
#
# 拉完后:
#   1. 检查 data/kb_corpus/ 下的 markdown
#   2. 用上传接口或 ingest 脚本把它们灌进 Milvus
#   3. 用 scripts/ingest_kb_corpus.py 导入 Milvus

# 不用 Stop, 因为 git 会向 stderr 写正常信息, 会被当成异常
$ErrorActionPreference = "Continue"

# 仓库清单: name = clone url
# 当前只拉一个最匹配 OnCall 场景的 repo: 940+ Prometheus 告警 + 处理建议
$Repos = @(
    @{ name = "awesome-prometheus-alerts"; url = "https://github.com/samber/awesome-prometheus-alerts.git" }
)

# 跳过这些文件名 (不当作知识库内容)
$SkipNames = @(
    "LICENSE", "LICENSE.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    "SECURITY.md", "CHANGELOG.md", "PULL_REQUEST_TEMPLATE.md",
    "ISSUE_TEMPLATE.md"
)

# 路径
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WorkDir = Join-Path $ProjectRoot ".kb_clone_tmp"
$OutDir = Join-Path $ProjectRoot "data\kb_corpus"

if (-not (Test-Path $WorkDir)) { New-Item -ItemType Directory -Path $WorkDir | Out-Null }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

Write-Host "========================================================"
Write-Host "  RAG 语料一键拉取"
Write-Host "  工作目录: $WorkDir"
Write-Host "  输出目录: $OutDir"
Write-Host "========================================================"

$TotalFiles = 0
$TotalBytes = 0
$DedupSkipped = 0
$Stats = @()

# 跨 repo 文件级去重: 用 SHA256 哈希记录已收录内容
$SeenHashes = @{}

function Get-ContentHash([string]$path) {
    # 标准化: 去 BOM + 统一换行 + 去首尾空白, 避免不同换行符导致 hash 不同
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $text = [System.Text.Encoding]::UTF8.GetString($bytes).Trim() -replace "`r`n", "`n"
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hashBytes = $sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($text))
    return ([System.BitConverter]::ToString($hashBytes) -replace '-', '').ToLower()
}

foreach ($r in $Repos) {
    $name = $r.name
    $url = $r.url
    $cloneDir = Join-Path $WorkDir $name
    $repoOut = Join-Path $OutDir $name

    Write-Host ""
    Write-Host "[clone] $name  from  $url"

    if (Test-Path $cloneDir) {
        Write-Host "  已存在, 跳过 clone (如需更新请删除 $cloneDir)"
    } else {
        # depth=1 浅克隆, 节省流量和磁盘
        # 把 stderr 重定向到 $null, 避免 git 的进度信息触发 NativeCommandError
        cmd /c "git clone --depth 1 $url `"$cloneDir`" 2>nul"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [error] clone 失败, 跳过" -ForegroundColor Red
            continue
        }
    }

    # 清空旧的输出目录
    if (Test-Path $repoOut) { Remove-Item -Recurse -Force $repoOut }
    New-Item -ItemType Directory -Path $repoOut | Out-Null

    # 拷贝所有 .md (扁平化, 名字加上路径前缀避免重名)
    $mdFiles = Get-ChildItem -Path $cloneDir -Recurse -Include *.md -File
    $count = 0
    $bytes = 0

    foreach ($f in $mdFiles) {
        if ($SkipNames -contains $f.Name) { continue }
        if ($f.Length -lt 200) { continue }   # 小于 200 字节当噪声

        # 文件级 hash 去重: 内容完全相同的文件只留一份
        $hash = Get-ContentHash $f.FullName
        if ($SeenHashes.ContainsKey($hash)) {
            $DedupSkipped++
            continue
        }
        $SeenHashes[$hash] = $f.FullName

        # 生成扁平化文件名: 子路径用 _ 连接, 避免冲突
        $rel = $f.FullName.Substring($cloneDir.Length + 1).Replace('\', '_').Replace('/', '_')
        $dest = Join-Path $repoOut $rel
        Copy-Item -Path $f.FullName -Destination $dest -Force
        $count++
        $bytes += $f.Length
    }

    Write-Host "  -> 抽取 $count 个 .md, $([math]::Round($bytes/1KB, 1)) KB"
    $TotalFiles += $count
    $TotalBytes += $bytes
    $Stats += [PSCustomObject]@{
        Repo = $name
        Files = $count
        SizeKB = [math]::Round($bytes / 1KB, 1)
    }
}

Write-Host ""
Write-Host "========================================================"
Write-Host "  统计"
Write-Host "========================================================"
$Stats | Format-Table -AutoSize
Write-Host ""
Write-Host "总计: $TotalFiles 个 .md 文件, $([math]::Round($TotalBytes/1MB, 2)) MB"
Write-Host "去重跳过 (内容完全相同的): $DedupSkipped 个"
Write-Host "输出位置: $OutDir"
Write-Host ""
Write-Host "下一步:"
Write-Host "  1. 检查 data\kb_corpus\<repo>\ 下的内容"
Write-Host "  2. 用 ingest 脚本批量入 Milvus, 或用 /api/v1/documents/upload 接口"
Write-Host "  3. 用 scripts\ingest_kb_corpus.py 导入 Milvus"
Write-Host ""
Write-Host "可选清理:"
Write-Host "  Remove-Item -Recurse -Force '$WorkDir'   # 删除 clone 临时目录"
