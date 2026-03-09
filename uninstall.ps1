#!/usr/bin/env pwsh
# skill-forge uninstaller for Windows

$ErrorActionPreference = "Stop"

function Main {
    $SkillDir = Join-Path $env:USERPROFILE ".claude" "skills"
    $AgentDir = Join-Path $env:USERPROFILE ".claude" "agents"

    Write-Host "=== Uninstalling skill-forge ===" -ForegroundColor Cyan
    Write-Host ""

    # Remove main skill
    $mainDir = Join-Path $SkillDir "skill-forge"
    if (Test-Path $mainDir) {
        Remove-Item -Recurse -Force $mainDir
        Write-Host "  Removed: $mainDir" -ForegroundColor Green
    }

    # Remove sub-skills
    $subSkills = @(
        "skill-forge-build", "skill-forge-convert", "skill-forge-evolve",
        "skill-forge-plan", "skill-forge-publish", "skill-forge-review"
    )
    foreach ($skill in $subSkills) {
        $skillPath = Join-Path $SkillDir $skill
        if (Test-Path $skillPath) {
            Remove-Item -Recurse -Force $skillPath
            Write-Host "  Removed: $skillPath" -ForegroundColor Green
        }
    }

    # Remove agents
    $agents = @("skill-forge-architect", "skill-forge-writer", "skill-forge-validator", "skill-forge-converter")
    foreach ($agent in $agents) {
        $agentPath = Join-Path $AgentDir "$agent.md"
        if (Test-Path $agentPath) {
            Remove-Item -Force $agentPath
            Write-Host "  Removed: $agentPath" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "=== skill-forge uninstalled ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Restart Claude Code to complete removal." -ForegroundColor Yellow
}

Main
