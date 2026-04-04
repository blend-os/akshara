import os
import subprocess


class RootFS:
    """Handles root filesystem operations.

    Attributes:
        rootfs_path: A string containing the path to the root filesystem
    """

    def __init__(self, rootfs_path: str, distro_config: dict, env: dict) -> None:
        """Initialises an instance based on a rootfs path and distro configuration.

        Args:
            rootfs: Path to root filesystem.
            distro_config: Dictionary containing distro configuration.
            env: Dictionary containing environment for command execution.
        """
        self.rootfs_path = rootfs_path
        self.distro_config = distro_config
        self.env = env

    def exists(self, path):
        """Checks if path exists within rootfs.

        Args:
            path: Path to check for.
        """
        return os.path.exists(os.path.join(self.rootfs_path, path))

    def exec_chroot(self, cmd, **kwargs) -> subprocess.CompletedProcess:
        """Runs command within rootfs using chroot.

        Args:
            cmd: List comprising command and arguments.
            **kwargs: Keyword arguments list for subprocess.run().
        """

        for dir in ("sys", "proc", "dev"):
            subprocess.run(
                [
                    "/sbin/mount",
                    "--bind",
                    f"/{dir}",
                    os.path.join(self.rootfs_path, dir),
                ]
            )

        completedProcess = subprocess.run(
            [
                "/sbin/chroot",
                self.rootfs_path,
            ]
            + list(cmd),
            **kwargs,
        )

        for dir in ("sys", "proc", "dev"):
            subprocess.run(["/sbin/umount", os.path.join(self.rootfs_path, dir)])

        return completedProcess

    def exec(self, cmd, **kwargs) -> subprocess.CompletedProcess:
        """Runs command within rootfs.

        Args:
            cmd: List comprising command and arguments.
            **kwargs: Keyword arguments list for subprocess.run().
        """
        return subprocess.run(
            [
                "/bin/systemd-nspawn",
                "--quiet",
                "--pipe",
                "--timezone=off",
                "--resolv-conf=bind-host",
                *[f"--setenv={name}={val}" for name, val in self.env.items()],
                "-D",
                self.rootfs_path,
            ]
            + list(cmd),
            **kwargs,
        )

    def __repr__(self) -> str:
        return self.rootfs_path
