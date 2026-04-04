#!/bin/sh

echo

# Attempt to remount rootfs as rw
mount -o remount,rw "$NEWROOT" >/dev/null 2>&1 || true

# Remove "$NEWROOT"/.successful-update if exists
rm -f "$NEWROOT"/.successful-update "$NEWROOT"/.update "$NEWROOT"/.tmp.boot

# Check if there is an available update
if [ -d "$NEWROOT"/.update_rootfs ]; then
    # Available, rename old /usr and move new /usr to /
    if [ -d "$NEWROOT"/.update_rootfs/usr ]; then
        rm -rf "$NEWROOT"/.old.usr
        mv "$NEWROOT"/usr "$NEWROOT"/.old.usr >/dev/null 2>&1
        mv "$NEWROOT"/.update_rootfs/usr "$NEWROOT"/usr
    fi

    # Same for /etc
    if [ -d "$NEWROOT"/.update_rootfs/etc ]; then
        rm -rf "$NEWROOT"/.old.etc
        mv "$NEWROOT"/etc "$NEWROOT"/.old.etc >/dev/null 2>&1
        mv "$NEWROOT"/.update_rootfs/etc "$NEWROOT"/etc
    fi

    # Same for /var
    if [ -d "$NEWROOT"/.update_rootfs/var ]; then
        rm -rf "$NEWROOT"/.old.var
        mv "$NEWROOT"/var "$NEWROOT"/.old.var >/dev/null 2>&1
        mv "$NEWROOT"/.update_rootfs/var "$NEWROOT"/var
    fi

    rm -rf "$NEWROOT"/.old.update_rootfs
    mv "$NEWROOT"/.update_rootfs "$NEWROOT"/.old.update_rootfs
    touch "$NEWROOT"/.successful-update
fi

# Handle immutable paths
if [ -f "$NEWROOT/usr/immutable.list" ]; then
    while IFS= read -r immutablepath; do mount -o ro,bind "$NEWROOT"/"$immutablepath" "$NEWROOT"/"$immutablepath" >/dev/null 2>&1 || true; done < "$NEWROOT"/usr/immutable.list
fi
