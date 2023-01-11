from typing import Optional
import bpy, pickle, os


path = bpy.utils.resource_path("USER")
path_cookiesFolder = os.path.join(path, "cookies")
path_cookies_username = os.path.join(path_cookiesFolder, "username")
path_cookies_tutorial_guide = os.path.join(path_cookiesFolder, "tutorial")


def remember_username(username: str) -> None:
    with open(path_cookies_username, "wb") as cookies_username:
        pickle.dump(username, cookies_username)


def read_remembered_username() -> Optional[str]:
    if not os.path.isfile(path_cookies_username):
        return ""
    with open(path_cookies_username, "rb") as fr:
        data = pickle.load(fr)
    return data


def delete_remembered_username() -> None:
    if os.path.isfile(path_cookies_username):
        os.remove(path_cookies_username)


def read_remembered_checkbox() -> bool:
    return os.path.isfile(path_cookies_username)


def remember_show_guide(self, context) -> None:
    # 순환 import 회피
    from ..lib.user_info import get_or_init_user_info

    user_info = get_or_init_user_info()
    prop = user_info.ACON_prop
    with open(path_cookies_tutorial_guide, "wb") as cookies_tutorial_guide:
        pickle.dump(prop.show_guide, cookies_tutorial_guide)


def read_remembered_show_guide() -> bool:
    if not os.path.isfile(path_cookies_tutorial_guide):
        return True
    with open(path_cookies_tutorial_guide, "rb") as fr:
        data = pickle.load(fr)
    return data
