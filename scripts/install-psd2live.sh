#!/usr/bin/env bash
# Download and integrity-check the latest official PSD2Live Linux x64 release.
# No sudo, no global PATH edits, no unverified remote shell execution.
set -euo pipefail

for exe in curl jq sha256sum tar mktemp; do
  command -v "$exe" >/dev/null 2>&1 || { echo "Missing executable: $exe" >&2; exit 1; }
done

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
release_info="$work_dir/release.json"
curl --fail --location --silent --show-error \
  https://api.github.com/repos/tsunehimatoi/psd2live/releases/latest \
  --output "$release_info"

release_tag="$(jq -er '.tag_name' "$release_info")"
asset="$(jq -ec '.assets[] | select(.name | endswith("-linux-x64.tar.gz"))' "$release_info" | head -n 1)"
[[ -n "$asset" ]] || { echo 'Linux x64 archive not found' >&2; exit 1; }
archive_name="$(jq -r '.name' <<< "$asset")"
archive_url="$(jq -r '.browser_download_url' <<< "$asset")"
archive_digest="$(jq -r '.digest // empty' <<< "$asset")"
[[ "$archive_digest" == sha256:* ]] || { echo 'Release has no SHA-256 digest. Refusing to install.' >&2; exit 1; }

archive_file="$work_dir/$archive_name"
echo "Downloading $archive_name ($release_tag)..."
curl --fail --location --show-error --progress-bar "$archive_url" --output "$archive_file"
printf '%s  %s\n' "${archive_digest#sha256:}" "$archive_file" | sha256sum --check --status
echo 'SHA-256 verified.'

install_dir="$HOME/.local/opt/psd2live/$release_tag"
if [[ -e "$install_dir" ]]; then
  echo "Already exists: $install_dir"
  echo 'No existing files were overwritten.'
else
  mkdir -p "$install_dir"
  tar -xzf "$archive_file" -C "$install_dir"
fi

launcher="$install_dir/PSD2Live/bin/PSD2Live"
if [[ ! -f "$launcher" ]]; then
  echo "Expected launcher missing: $launcher" >&2
  echo 'Inspect the downloaded archive layout before running anything.' >&2
  exit 1
fi

printf '\nInstalled under: %s\nLaunch with:\n  %q\n' "$install_dir" "$launcher"
echo 'Keep PSD2Live open so Codex can communicate with its MCP server.'
