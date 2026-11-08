#!/bin/sh
# Replace the example values before running this task on a NAS.
MAC='02:11:22:33:44:55'
IFACE='eth0'
SYNONET='/usr/syno/sbin/synonet'

if [ "${1:-}" = '--dry-run' ]; then
    printf 'DRY RUN: %s --wake %s %s\n' "$SYNONET" "$MAC" "$IFACE"
    exit 0
fi

if [ ! -x "$SYNONET" ]; then
    printf 'ERROR: executable not found: %s\n' "$SYNONET" >&2
    exit 127
fi

printf 'Requesting WOL: MAC=%s interface=%s\n' "$MAC" "$IFACE"
"$SYNONET" --wake "$MAC" "$IFACE"
result=$?
printf 'synonet exit code: %s\n' "$result"
exit "$result"
