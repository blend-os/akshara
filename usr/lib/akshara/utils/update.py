import filecmp
import os
import subprocess
import sys
from pathlib import Path

from classes.rootfs import RootFS
from utils import output, users

from . import helpers
from .gen_rootfs import gen_rootfs


def update_cleanup() -> None:
    """Clean-up from previous rebase/update."""

    for path in (
        "/var/cache/akshara/rootfs/sys",
        "/var/cache/akshara/rootfs/proc",
        "/var/cache/akshara/rootfs/dev",
        "/var/cache/akshara/rootfs/var/cache/blendOS",
    ):
        subprocess.run(
            ["/sbin/umount", "-l", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    subprocess.run(
        [
            "/bin/rm",
            "-rf",
            "/var/cache/akshara/rootfs",
            "/.update_rootfs",
            "/.old.update_rootfs",
            "/.boot.bkp",
        ]
    )


def merge_etc(new_rootfs: RootFS, overrides_keep_new: dict) -> None:
    """Merges /etc trees.

    Args:
        new_rootfs: New RootFS instance.
        overrides_keep_new: Dictionary comprising overrides and whether to keep new.
    """
    if not os.path.isdir("/usr/etc"):
        subprocess.run(["/bin/rm", "-rf", "/usr/etc"])
        subprocess.run(["/bin/cp", "-ax", "/etc", "/usr/etc"])

    etc_diff = filecmp.dircmp("/etc/", "/usr/etc/")

    def handle_diff_etc_files(dcmp):
        dir_name = dcmp.left.replace("/etc/", f"{new_rootfs}/etc/", 1)
        subprocess.run(["/bin/mkdir", "-p", dir_name])
        for name in dcmp.left_only:
            subprocess.run(
                ["/bin/cp", "-ax", "--", os.path.join(dcmp.left, name), dir_name]
            )
        for name in dcmp.diff_files:
            subprocess.run(["/bin/rm", "-f", "--", os.path.join(dir_name, name)])
            subprocess.run(
                ["/bin/cp", "-ax", "--", os.path.join(dcmp.left, name), dir_name]
            )
        for sub_dcmp in dcmp.subdirs.values():
            handle_diff_etc_files(sub_dcmp)

    handle_diff_etc_files(etc_diff)

    for override, keep_new in overrides_keep_new.items():
        if (
            override.startswith("/etc/")
            and os.path.exists(override)
            and new_rootfs.exists(override)
        ):
            subprocess.run(["/bin/rm", "-rf", f"{new_rootfs}/{override}"])
            if keep_new:
                subprocess.run(
                    [
                        "/bin/cp",
                        "-ax",
                        f"{new_rootfs}/usr/{override}",
                        f"{new_rootfs}/{override}",
                    ]
                )
            else:
                subprocess.run(
                    [
                        "/bin/cp",
                        "-ax",
                        override,
                        f"{new_rootfs}/{override}",
                    ]
                )


def merge_var(new_rootfs: RootFS, overrides_keep_new: dict) -> None:
    """Merges /var trees.

    Args:
        new_rootfs: Path to rootfs.
        overrides_keep_new: Dictionary comprising overrides and whether to keep new.
    """
    subprocess.run(["/bin/rm", "-rf", f"{new_rootfs}/var/lib"])
    subprocess.run(["/bin/cp", "-ax", "/var/lib", f"{new_rootfs}/var/lib"])

    var_lib_diff = filecmp.dircmp(
        f"{new_rootfs}/usr/var/lib/", f"{new_rootfs}/var/lib/"
    )

    dir_name = f"{new_rootfs}/var/lib/"
    for name in var_lib_diff.left_only:
        if os.path.isdir(os.path.join(var_lib_diff.left, name)):
            subprocess.run(
                ["/bin/cp", "-ax", os.path.join(var_lib_diff.left, name), dir_name]
            )

    for override, keep_new in overrides_keep_new.items():
        if (
            override.startswith("/var/")
            and os.path.exists(override)
            and new_rootfs.exists(override)
        ):
            subprocess.run(["/bin/rm", "-rf", f"{new_rootfs}/{override}"])
            if keep_new:
                subprocess.run(
                    [
                        "/bin/cp",
                        "-ax",
                        f"{new_rootfs}/usr/{override}",
                        f"{new_rootfs}/{override}",
                    ]
                )
            else:
                subprocess.run(
                    [
                        "/bin/cp",
                        "-ax",
                        override,
                        f"{new_rootfs}/{override}",
                    ]
                )


def merge_into_tree(
    tree_root: str, tmp_tree_root: str, copy_symlinks: bool = True
) -> None:
    """Merge a new tree into an existing tree.

    Args:
        tree_root: String containing path to existing tree.
        tmp_tree_root: String containing path to new tree.
        copy_symlinks: Whether to copy symlinks.
    """

    new_paths = []
    for tmp_root, _, files in os.walk(tmp_tree_root):
        root = tmp_root.replace(tmp_tree_root, tree_root, 1)
        subprocess.run(["/bin/mkdir", "-p", root])
        new_paths.append(root)
        for path in files:
            subprocess.run(["/bin/rm", "-rf", "--", os.path.join(root, path)])
            if copy_symlinks:
                subprocess.run(
                    [
                        "/bin/cp",
                        "-ax",
                        os.path.join(tmp_root, path),
                        os.path.join(root, path),
                    ]
                )
            else:
                if os.path.islink(os.path.join(tmp_root, path)):
                    output.info(
                        f"not merging {os.path.join(root, path)} as it is a symlink"
                    )
                    continue
                else:
                    subprocess.run(
                        [
                            "/bin/cp",
                            "-ax",
                            os.path.join(tmp_root, path),
                            os.path.join(root, path),
                        ]
                    )
            new_paths.append(os.path.join(root, path))

    for root, _, files in os.walk(tree_root):
        for path in files:
            if os.path.join(root, path) not in new_paths:
                subprocess.run(["/bin/rm", "-rf", "--", os.path.join(root, path)])


def handle_boot(new_rootfs: RootFS, boot_config: dict) -> None:
    """Handles /boot partition."""

    subprocess.run(["/bin/rm", "-rf", "/.boot.bkp"])
    subprocess.run(["/bin/cp", "-ax", "/boot", "/.boot.bkp"])

    # Replace contents of /boot with those from new rootfs
    # FIXME: should be atomic
    merge_into_tree("/boot", os.path.join(str(new_rootfs), "boot"), False)

    subprocess.run(["/sbin/mount", "--bind", "/boot", f"{new_rootfs}/boot"])

    def restore_old_boot():
        subprocess.run(
            ["/sbin/umount", "-l", f"{new_rootfs}/boot"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        merge_into_tree("/boot", "/.boot.bkp")
        subprocess.run(["/bin/rm", "-rf", "/.boot.bkp"])
        subprocess.run(["mv", "/.update_rootfs", "/.old.update_rootfs"])

    if boot_config["type"] == "bios":
        if boot_config["loader"] == "grub":
            if (
                new_rootfs.exec_chroot(
                    [
                        "/sbin/grub-install",
                        "--target=i386-pc",
                        boot_config["device"],
                    ]
                ).returncode
                != 0
            ):
                restore_old_boot()
                output.error("failed to install GRUB")
                output.error("aborted update")
                exit(1)
        else:
            restore_old_boot()
            output.error("unsupported bootloader for BIOS configuration")
            output.error("aborted update")
            exit(1)
    elif boot_config["type"] == "uefi":
        if boot_config["loader"] == "grub":
            efi_directory = "/boot/efi" if os.path.isdir("/boot/efi/EFI") else "/boot"
            if (
                new_rootfs.exec_chroot(
                    [
                        "/sbin/grub-install",
                        f"--efi-directory={efi_directory}",
                        "--target=x86_64-efi",
                        "--removable",
                        "--bootloader-id=blendOS",
                    ]
                ).returncode
                != 0
            ):
                restore_old_boot()
                output.error("failed to install GRUB")
                output.error("aborted update")
                exit(1)
        else:
            restore_old_boot()
            output.error("unsupported bootloader for BIOS configuration")
            output.error("aborted update")
            exit(1)
    else:
        restore_old_boot()
        output.error(f"unsupported system type - {boot_config['type']}")
        output.error("aborted update")
        exit(1)

    if boot_config["loader"] == "grub":
        new_rootfs.exec_chroot(["/sbin/grub-mkconfig", "-o", "/boot/grub/grub.cfg"])
        new_rootfs.exec_chroot(["/bin/cp", "/boot/grub/grub.cfg", "/boot/grub.cfg"])

    subprocess.run(
        ["/sbin/umount", "-l", f"{new_rootfs}/boot"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(["/bin/rm", "-rf", "/.boot.bkp"])


def update() -> None:
    """Update system.

    Args:
        image_name: Name of image to rebase to.
    """

    update_cleanup()

    system_config = helpers.get_system_config()

    output.info("generating new rootfs")

    subprocess.run(["/bin/rm", "-rf", "/var/cache/akshara"])
    Path("/var/cache/akshara/rootfs").mkdir(parents=True, exist_ok=True)

    new_rootfs = gen_rootfs(system_config, "/var/cache/akshara/rootfs")

    if (
        len(
            [
                kernel
                for kernel in os.listdir(f"{new_rootfs}/boot")
                if kernel.startswith("vmlinuz")
            ]
        )
        == 0
    ):
        output.error("new rootfs contains no kernel")
        output.error("refusing to proceed with applying update")
        exit(1)

    overrides_keep_new = (
        {
            override["path"]: override["keep"] == "new"
            for override in system_config["override"]
            if isinstance(override.get("keep"), str)
        }
        if isinstance(system_config.get("override"), list)
        else {}
    )

    overrides_keep_new["/var/cache/blendOS"] = False

    output.info("merging /etc...")
    merge_etc(new_rootfs, overrides_keep_new)

    try:
        # Store new_passwd_entries for users.merge_group() call
        new_passwd_entries = users.merge_passwd(new_rootfs)
    except Exception:
        output.error("malformed /etc/passwd")
        sys.exit(1)

    try:
        users.merge_shadow(new_rootfs)
    except Exception:
        output.error("malformed /etc/shadow")
        sys.exit(1)

    try:
        users.merge_group(new_rootfs, new_passwd_entries)
    except Exception:
        output.error("malformed /etc/group")
        sys.exit(1)

    try:
        users.merge_gshadow(new_rootfs, new_passwd_entries)
    except Exception:
        output.error("malformed /etc/shadow")
        sys.exit(1)

    output.info("merging /var...")
    merge_var(new_rootfs, overrides_keep_new)

    subprocess.run(["/bin/cp", "-ax", str(new_rootfs), "/.update_rootfs"])

    handle_boot(new_rootfs, system_config["boot"])

    print()
