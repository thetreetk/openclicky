#!/usr/bin/env bash
# Populate AppResources/OpenClicky/CodexRuntime from a local Codex install.
# CodexRuntime is gitignored (large vendor binary); Agent Mode needs it locally.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${ROOT}/AppResources/OpenClicky/CodexRuntime"

ARCH="$(uname -m)"
case "${ARCH}" in
  arm64) VENDOR_ARCH="aarch64-apple-darwin" ;;
  x86_64) VENDOR_ARCH="x86_64-apple-darwin" ;;
  *)
    echo "Unsupported architecture: ${ARCH}" >&2
    exit 1
    ;;
esac

resolve_codex_bin() {
  if [[ -n "${OPENCLICKY_CODEX_BIN:-}" && -x "${OPENCLICKY_CODEX_BIN}" ]]; then
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${OPENCLICKY_CODEX_BIN}"
    return
  fi
  if command -v codex >/dev/null 2>&1; then
    python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$(command -v codex)"
    return
  fi
  for candidate in \
    /opt/homebrew/bin/codex \
    /usr/local/bin/codex \
    /Applications/Codex.app/Contents/Resources/codex \
    "${HOME}/Applications/Codex.app/Contents/Resources/codex"
  do
    if [[ -x "${candidate}" ]]; then
      python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${candidate}"
      return
    fi
  done
  return 1
}

if ! SRC="$(resolve_codex_bin)"; then
  echo "Could not find a local codex executable." >&2
  echo "Install Codex (e.g. brew install --cask codex) or set OPENCLICKY_CODEX_BIN." >&2
  exit 1
fi

SRC_ROOT="$(cd "$(dirname "${SRC}")/.." && pwd)"
mkdir -p "${DEST}/bin" \
  "${DEST}/vendor/${VENDOR_ARCH}/codex" \
  "${DEST}/vendor/${VENDOR_ARCH}/path"

/usr/bin/ditto "${SRC}" "${DEST}/bin/codex"
/usr/bin/ditto "${SRC}" "${DEST}/vendor/${VENDOR_ARCH}/codex/codex"
chmod +x "${DEST}/bin/codex" "${DEST}/vendor/${VENDOR_ARCH}/codex/codex"

if [[ -x "${SRC_ROOT}/codex-path/rg" ]]; then
  /usr/bin/ditto "${SRC_ROOT}/codex-path/rg" "${DEST}/vendor/${VENDOR_ARCH}/path/rg"
  chmod +x "${DEST}/vendor/${VENDOR_ARCH}/path/rg"
fi

if [[ -x "${SRC_ROOT}/bin/codex-code-mode-host" ]]; then
  /usr/bin/ditto "${SRC_ROOT}/bin/codex-code-mode-host" "${DEST}/bin/codex-code-mode-host"
  chmod +x "${DEST}/bin/codex-code-mode-host"
fi

echo "Synced Codex runtime from ${SRC}"
echo "  -> ${DEST}/bin/codex"
echo "  -> ${DEST}/vendor/${VENDOR_ARCH}/codex/codex"
"${DEST}/bin/codex" --version || true
