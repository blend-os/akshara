import json
import os
import subprocess

from classes.rootfs import RootFS

from . import output


def run_script_rootfs(rootfs: RootFS, input: str, args: list):
    """Runs a script within the rootfs."""

    rootfs.exec(["bash", "-s", *args], text=True, input=input)


def gen_rootfs(system_config: dict, rootfs_path: str, use_cache: bool = True) -> RootFS:
    """Generates a rootfs for a given system configuration."""

    rootfs = RootFS(rootfs_path, system_config["distro-config"], system_config["env"])

    subprocess.run(["mkdir", "-p", f"{rootfs_path}/var/cache/blendOS"])

    if use_cache:
        subprocess.run(["mkdir", "-p", "/var/cache/blendOS"])
        subprocess.run(["mount", "--bind", "/var/cache/blendOS", f"{rootfs_path}/var/cache/blendOS"])

    if (
        subprocess.run(
            ["bash", "-s"],
            text=True,
            input=system_config["distro-config"]["initialise"],
            cwd=rootfs_path,
            env=os.environ.copy() | system_config["env"],
        ).returncode
        != 0
    ):
        output.error("failed to initialise rootfs")
        exit(1)

    modules = {}

    for module in system_config["modules"]:
        modules[module["name"]] = module["run"]

    for stage in system_config["stages"] + system_config["post-stages"]:
        if stage.get("module") not in modules.keys():
            output.error(f"{stage.get('module')} not found within module list.")
            exit(1)

        inputs = stage["inputs"] if isinstance(stage.get("inputs"), list) else []
        run_script_rootfs(rootfs, modules[stage["module"]], inputs)

    if (
        subprocess.run(
            ["bash", "-s"],
            text=True,
            input=system_config["distro-config"]["finalise"],
            cwd=str(rootfs_path),
            env=os.environ.copy() | system_config["env"],
        ).returncode
        != 0
    ):
        output.error("failed to finalise rootfs")
        exit(1)

    with open(os.path.join(rootfs_path, "usr/system.json"), "w") as system_json_file:
        json.dump(system_config, system_json_file, ensure_ascii=False)
        pass

    with open(
        os.path.join(str(rootfs), "usr/immutable.list"), "w"
    ) as immutable_list_file:
        immutable_set = set(
            [
                override["path"]
                for override in system_config["override"]
                if isinstance(override.get("immutable"), bool) and override["immutable"]
            ]
            if isinstance(system_config.get("override"), list)
            else {}
        )

        immutable_set.add("/usr")

        immutable_list_file.write("\n".join(list(immutable_set)))

    subprocess.run(["cp", "-ax", f"{rootfs}/etc", f"{rootfs}/usr/etc"])
    subprocess.run(["cp", "-ax", f"{rootfs}/var", f"{rootfs}/usr/var"])

    if use_cache:
        subprocess.run(["umount", "-l", f"{rootfs}/var/cache/blendOS"])

    return rootfs
