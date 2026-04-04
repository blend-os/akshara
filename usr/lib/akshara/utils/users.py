def merge_passwd(new_rootfs) -> list:
    """Merge /etc/passwd from host and new rootfs.

    Args:
        new_rootfs: Path to new root filesystem.

    Returns:
        A list of the newly generated passwd entries.
    """

    with open("/etc/passwd") as f:
        current_passwd_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/usr/etc/passwd") as f:
        current_system_passwd_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open(f"{new_rootfs}/usr/etc/passwd") as f:
        new_rootfs_passwd_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    new_passwd_entries = list(new_rootfs_passwd_entries.values())

    for user in set(current_passwd_entries.keys()) - set(
        current_system_passwd_entries.keys()
    ):
        if (
            int(current_passwd_entries[user].split(":")[2]) >= 1000
            and user not in new_rootfs_passwd_entries.keys()
        ):
            new_passwd_entries.append(current_passwd_entries[user])

    with open(f"{new_rootfs}/etc/passwd", "w") as f:
        for user in new_passwd_entries:
            f.write(user + "\n")

    return new_passwd_entries


def merge_shadow(new_rootfs):
    """Merge /etc/shadow from host and new rootfs.

    Args:
        new_rootfs: Path to new root filesystem.
    """

    with open("/etc/passwd") as f:
        current_passwd_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/etc/shadow") as f:
        current_shadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/usr/etc/shadow") as f:
        current_system_shadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open(f"{new_rootfs}/usr/etc/shadow") as f:
        new_rootfs_shadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    new_shadow_entries = list(new_rootfs_shadow_entries.values())

    for user in set(current_shadow_entries.keys()) - set(
        current_system_shadow_entries.keys()
    ):
        if (
            int(current_passwd_entries[user].split(":")[2]) >= 1000
            and user not in new_rootfs_shadow_entries.keys()
        ):
            new_shadow_entries.append(current_shadow_entries[user])

    with open(f"{new_rootfs}/etc/shadow", "w") as f:
        for user in new_shadow_entries:
            f.write(user + "\n")


def merge_group(new_rootfs, new_passwd_entries):
    """Merge /etc/group from host and new rootfs.

    Args:
        new_rootfs: Path to new root filesystem.
    """

    with open("/etc/group") as f:
        current_group_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/usr/etc/group") as f:
        current_system_group_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open(f"{new_rootfs}/usr/etc/group") as f:
        new_rootfs_group_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    new_group_entries_names = list(
        set(new_rootfs_group_entries.keys()) - set(current_system_group_entries.keys())
    )
    new_group_entries = [
        new_rootfs_group_entries[new_group_entries_name]
        for new_group_entries_name in new_group_entries_names
    ]

    for group in (
        set(current_system_group_entries.keys()) & set(new_rootfs_group_entries.keys())
    ) & set(current_group_entries.keys()):
        old_group_entry = current_group_entries[group]
        new_group_entry = new_rootfs_group_entries[group]
        for member_user in old_group_entry.split(":")[3].split(","):
            if member_user in [
                passwd_entry.split(":")[0] for passwd_entry in new_passwd_entries
            ] and member_user not in new_group_entry.split(":")[3].split(","):
                if new_group_entry.split(":")[3] == "":
                    new_group_entry += member_user
                else:
                    new_group_entry += "," + member_user
        new_group_entries.append(new_group_entry)

    for group in set(current_group_entries.keys()) - set(
        current_system_group_entries.keys()
    ):
        if (
            int(current_group_entries[group].split(":")[2]) >= 1000
            and group not in new_rootfs_group_entries.keys()
        ):
            new_group_entries.append(current_group_entries[group])

    with open(f"{new_rootfs}/etc/group", "w") as f:
        for group in new_group_entries:
            f.write(group + "\n")


def merge_gshadow(new_rootfs, new_passwd_entries):
    """Merge /etc/gshadow from host and new rootfs.

    Args:
        new_rootfs: Path to new root filesystem.
    """

    with open("/etc/group") as f:
        current_group_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/etc/gshadow") as f:
        current_gshadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open("/usr/etc/gshadow") as f:
        current_system_gshadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    with open(f"{new_rootfs}/usr/etc/gshadow") as f:
        new_rootfs_gshadow_entries = {
            line.strip().split(":")[0]: line.strip() for line in f if line.strip()
        }

    new_gshadow_entries_names = list(
        set(new_rootfs_gshadow_entries.keys())
        - set(current_system_gshadow_entries.keys())
    )
    new_gshadow_entries = [
        new_rootfs_gshadow_entries[new_gshadow_entries_name]
        for new_gshadow_entries_name in new_gshadow_entries_names
    ]

    for group in (
        set(current_system_gshadow_entries.keys())
        & set(new_rootfs_gshadow_entries.keys())
    ) & set(current_gshadow_entries.keys()):
        old_gshadow_entry = current_gshadow_entries[group]
        new_gshadow_entry = new_rootfs_gshadow_entries[group]
        for member_user in old_gshadow_entry.split(":")[3].split(","):
            if member_user in [
                passwd_entry.split(":")[0] for passwd_entry in new_passwd_entries
            ] and member_user not in new_gshadow_entry.split(":")[3].split(","):
                if new_gshadow_entry.split(":")[3] == "":
                    new_gshadow_entry += member_user
                else:
                    new_gshadow_entry += "," + member_user
        new_gshadow_entries.append(new_gshadow_entry)

    for group in set(current_gshadow_entries.keys()) - set(
        current_system_gshadow_entries.keys()
    ):
        if (
            int(current_group_entries[group].split(":")[2]) >= 1000
            and group not in new_rootfs_gshadow_entries.keys()
        ):
            new_gshadow_entries.append(current_gshadow_entries[group])

    with open(f"{new_rootfs}/etc/gshadow", "w") as f:
        for group in new_gshadow_entries:
            f.write(group + "\n")
