#!/usr/bin/env bash
set -u

echo '=== Host environment ==='
printf 'Session: %s\nDesktop: %s\nDISPLAY: %s\n' "${XDG_SESSION_TYPE:-unknown}" "${XDG_CURRENT_DESKTOP:-unknown}" "${DISPLAY:-unset}"

echo
echo '=== Executables ==='
for exe in git curl jq python uv codex glxinfo ffmpeg nvidia-smi; do
  if command -v "$exe" >/dev/null 2>&1; then
    printf 'OK      %-14s %s\n' "$exe" "$(command -v "$exe")"
  else
    printf 'MISSING %s\n' "$exe"
  fi
done

echo
echo '=== GPU ==='
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1 || true
fi

echo
echo '=== GLX (if XWayland DISPLAY is available) ==='
if [[ -n "${DISPLAY:-}" ]] && command -v glxinfo >/dev/null 2>&1; then
  glxinfo -B 2>&1 | grep -E 'OpenGL vendor|OpenGL renderer|OpenGL version|Error|error' || true
else
  echo 'Skipped: DISPLAY or glxinfo unavailable'
fi

echo
echo '=== Codex MCP registrations ==='
if command -v codex >/dev/null 2>&1; then
  codex mcp list 2>&1 || true
fi

echo
echo 'This script only inspects the system; it makes no changes.'
