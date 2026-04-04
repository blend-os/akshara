import json
import os
import subprocess

import requests
import yaml

from . import output


def resolve_config(system_config: dict) -> dict:
    if system_config["track"] == "base":
        try:
            return {
                "track": "base",
                "modules": system_config["modules"]
                if isinstance(system_config.get("modules"), list)
                else [],
                "stages": system_config["stages"]
                if isinstance(system_config.get("stages"), list)
                else [],
                "post-stages": system_config["post-stages"]
                if isinstance(system_config.get("post-stages"), list)
                else [],
                "override": system_config["override"]
                if isinstance(system_config.get("override"), list)
                else [],
                "needs-update": system_config["needs-update"]
                if isinstance(system_config.get("needs-update"), list)
                else [],
                "env": system_config["env"]
                if isinstance(system_config.get("env"), dict)
                else {},
                "distro-config": system_config["distro-config"],
                "auto-update": system_config["auto-update"]
                if isinstance(system_config.get("auto-update"), dict)
                else {"enabled": False},
                "boot": system_config["boot"],
            }
        except IndexError:
            output.error("base track must include distro-config")
            exit(1)
    else:
        base_track_src = system_config["track"]
        if os.path.exists(base_track_src):
            base_config = resolve_config(yaml.safe_load(base_track_src))
        elif base_track_src.startswith("http:") or base_track_src.startswith("https:"):
            base_config = resolve_config(
                yaml.safe_load(
                    requests.get(base_track_src, allow_redirects=True).content.decode()
                )
            )
            pass
        else:
            output.error(f"could not resolve parent track - {system_config['track']}")
            exit(1)

        base_config["modules"] += (
            system_config["modules"]
            if isinstance(system_config.get("modules"), list)
            else []
        )

        base_config["stages"] += (
            system_config["stages"]
            if isinstance(system_config.get("stages"), list)
            else []
        )

        base_config["post-stages"] = (
            system_config["post-stages"]
            if isinstance(system_config.get("post-stages"), list)
            else []
        ) + base_config["post-stages"]

        base_config["override"] += (
            system_config["override"]
            if isinstance(system_config.get("override"), list)
            else []
        )

        base_config["needs-update"] += (
            system_config["needs-update"]
            if isinstance(system_config.get("needs-update"), list)
            else []
        )

        base_config["env"] = (
            base_config["env"] | system_config["env"]
            if isinstance(system_config.get("env"), dict)
            else base_config["env"]
        )

        base_config["auto-update"] = (
            system_config["auto-update"]
            if isinstance(system_config.get("auto-update"), dict)
            else base_config["auto-update"]
        )

        base_config["boot"] = (
            system_config["boot"]
            if isinstance(system_config.get("boot"), dict)
            else base_config["boot"]
        )

        return base_config


def get_system_config():
    if os.path.exists("/system.yaml"):
        with open("/system.yaml") as system_yaml_file:
            system_config = yaml.safe_load(system_yaml_file.read())
    elif os.path.exists("/system.yml"):
        with open("/system.yml") as system_yml_file:
            system_config = yaml.safe_load(system_yml_file.read())
    elif os.path.exists("/system.json"):
        with open("/system.json") as system_json_file:
            system_config = json.load(system_json_file)
    else:
        output.error("no system config file found")
        exit(1)

    return resolve_config(system_config)


def get_installed_system_config():
    with open("/usr/system.json") as usr_system_json_file:
        return json.load(usr_system_json_file)


def is_already_latest() -> bool:
    """Checks if system is already up-to-date.

    Returns:
        True if up-to-date, else False.
    """

    if os.path.isfile("/usr/system.json"):
        with open("/usr/system.json") as system_json_file:
            contents = system_json_file.read().strip()
            system_config = get_system_config()
            if (
                json.dumps(system_config, ensure_ascii=False).strip()
                == contents.strip()
            ):
                if len(system_config["needs-update"]) == 0:
                    return False

                for update_check in system_config["needs-update"]:
                    if (
                        subprocess.run(
                            ["bash", "-s"],
                            text=True,
                            input=update_check,
                            env=os.environ.copy() | system_config["env"],
                        ).returncode
                        == 0
                    ):
                        return False

                return True
            else:
                return False
    else:
        return False


def notify_prompt(title: str, body: str, actions: dict) -> str:
    """Display a notification prompting the user.

    Args:
        title: Title of the notification.
        body: Body of the notification.
        actions: Dict containing action key-value pairs.

    Returns:
        String containing selected action.
    """
    return (
        subprocess.run(
            [
                "notify-send",
                "--app-name=System",
                "--urgency=critical",
                title,
                body,
                *[f"--action={action}={actions[action]}" for action in actions.keys()],
            ],
            stdout=subprocess.PIPE,
        )
        .stdout.decode()
        .strip()
    )
