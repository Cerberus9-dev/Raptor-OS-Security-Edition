#!/usr/bin/env bash
set -euo pipefail

ERRORS=0

echo "==> [1/3] Enforcing & Verifying Executable Permissions..."
# Ensure binaries and hooks are executable
chmod +x build/config/includes.chroot/usr/local/bin/* 2>/dev/null || true
chmod +x build/config/hooks/live/*.hook.chroot 2>/dev/null || true

for script in build/config/includes.chroot/usr/local/bin/*; do
  if [ -f "$script" ] && [ ! -x "$script" ]; then
    echo "  [ERROR] Failed to set executable bit: $script"
    ERRORS=$((ERRORS + 1))
  fi
done

for hook in build/config/hooks/live/*.hook.chroot; do
  if [ -f "$hook" ] && [ ! -x "$hook" ]; then
    echo "  [ERROR] Failed to set hook executable bit: $hook"
    ERRORS=$((ERRORS + 1))
  fi
done

echo "==> [2/3] Validating Script & Policy Syntax..."
for sh_file in build/config/includes.chroot/usr/local/bin/*; do
  if file "$sh_file" | grep -q "POSIX shell script"; then
    bash -n "$sh_file" || ERRORS=$((ERRORS + 1))
  fi
done

POLICIES_JSON="build/config/includes.chroot/etc/librewolf/policies/policies.json"
if [ -f "$POLICIES_JSON" ]; then
  python3 -m json.tool "$POLICIES_JSON" >/dev/null 2>&1 || ERRORS=$((ERRORS + 1))
fi

echo "==> [3/3] Checking Package List Isolation..."
EXTRA_LISTS=$(find build/config/package-lists/ -type f ! -name 'raptor-security.list.chroot' | wc -l)
if [ "$EXTRA_LISTS" -gt 0 ]; then
  echo "  [ERROR] Redundant package list files found in build/config/package-lists/"
  ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "❌ Validation failed with $ERRORS error(s)."
  exit 1
fi
echo "✅ All pre-build checks passed successfully."
