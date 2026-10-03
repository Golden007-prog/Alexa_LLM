<#
.SYNOPSIS
    Deploy this repo's skill to its Alexa-hosted twin (development stage only).

.DESCRIPTION
    Copies lambda/ and skill-package/ from this repo into the hosted-skill
    clone made by `ask init --hosted-skill-id <id>`, commits there, and runs
    `git push origin master`. Alexa-hosted turns a push to master into a
    deploy to the DEVELOPMENT stage; it never touches the live stage.

    lambda/config.json in the hosted clone is never overwritten or deleted,
    so an API key kept there never passes through GitHub.

.EXAMPLE
    .\scripts\deploy-hosted.ps1 -DryRun     # show what would change
    .\scripts\deploy-hosted.ps1             # copy, commit, confirm, push
#>
[CmdletBinding()]
param(
    [string]$HostedPath = "E:\Alexa NLP\hosted-skill",
    [string]$Message = "",
    [switch]$DryRun,
    [switch]$Yes
)

# Not "Stop": git writes harmless warnings (line endings, progress) to stderr,
# which Windows PowerShell would turn into terminating errors. Exit codes are
# checked explicitly instead.
$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent $PSScriptRoot

function Fail([string]$text) {
    Write-Host "ERROR: $text" -ForegroundColor Red
    exit 1
}

function Mirror([string]$from, [string]$to, [string[]]$mode) {
    $quiet = @("/NJH", "/NJS", "/NP", "/NDL")
    if ($DryRun) { $quiet += "/L" } else { $quiet += "/NFL" }
    robocopy $from $to @mode @quiet | Out-Host
    if ($LASTEXITCODE -ge 8) { Fail "robocopy $from failed (exit $LASTEXITCODE)" }
}

if (-not (Test-Path (Join-Path $HostedPath ".git"))) {
    Fail "No git clone at '$HostedPath'. From E:\Alexa NLP run: ask init --hosted-skill-id <your skill id>"
}
$branch = (git -C $HostedPath rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "master") {
    Fail "The hosted clone is on '$branch'. Run: git -C `"$HostedPath`" checkout master"
}
if (git -C $HostedPath status --porcelain) {
    Fail "The hosted clone has uncommitted changes. Commit or stash them first."
}
if (git -C $repo status --porcelain -- lambda skill-package) {
    Fail "lambda/ or skill-package/ has uncommitted changes here. Commit (and test) first."
}

$sha = (git -C $repo rev-parse --short HEAD).Trim()
Write-Host "Deploying Alexa_LLM $sha -> $HostedPath (master)" -ForegroundColor Cyan

# lambda/ is mirrored (files removed here are removed there) except
# config.json; skill-package/ is copied without deleting hosted-only files.
Mirror (Join-Path $repo "lambda") (Join-Path $HostedPath "lambda") @("/MIR", "/XF", "config.json", "*.pyc", "/XD", "__pycache__")
Mirror (Join-Path $repo "skill-package") (Join-Path $HostedPath "skill-package") @("/E")
# Same line-ending rule as this repo, so CRLF never reaches Lambda files.
Mirror $repo $HostedPath @(".gitattributes")

if ($DryRun) {
    Write-Host "Dry run: the files above would be copied. Nothing was changed." -ForegroundColor Yellow
    exit 0
}

git -C $HostedPath add -A -- lambda skill-package .gitattributes
if ($LASTEXITCODE -ne 0) { Fail "git add failed" }
if (-not (git -C $HostedPath status --porcelain)) {
    Write-Host "The hosted clone already matches $sha. Nothing to deploy."
    exit 0
}
git -C $HostedPath status --short
if (-not $Message) { $Message = "Deploy Alexa_LLM $sha" }
git -C $HostedPath commit -q -m $Message
if ($LASTEXITCODE -ne 0) { Fail "git commit failed" }

if (-not $Yes) {
    $answer = Read-Host "Push to master now? This deploys to the DEVELOPMENT stage. [y/N]"
    if ($answer -notin @("y", "Y", "yes")) {
        Write-Host "Committed but not pushed. Push later with: git -C `"$HostedPath`" push origin master"
        exit 0
    }
}
git -C $HostedPath push origin master
if ($LASTEXITCODE -ne 0) { Fail "git push failed" }

$states = Join-Path $HostedPath ".ask\ask-states.json"
$skillId = $null
if (Test-Path $states) {
    $skillId = (Get-Content $states -Raw | ConvertFrom-Json).profiles.default.skillId
}
if ($skillId -and (Get-Command ask -ErrorAction SilentlyContinue)) {
    Write-Host "Build status (the interaction model rebuilds after each push):" -ForegroundColor Cyan
    ask smapi get-skill-status -s $skillId
} else {
    Write-Host "Pushed. Check the build in the Developer Console: Build tab."
}
