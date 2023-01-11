import requests
import logging
import os
import os.path
import sys
from typing import Tuple, Optional
from distutils.version import StrictVersion
import configparser
from AblerLauncherUtils import *


if sys.platform == "win32":
    from win32com.client import Dispatch

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

LOG_FORMAT = (
    "%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
)
os.makedirs(get_datadir() / "Blender/2.96", exist_ok=True)
os.makedirs(get_datadir() / "Blender/2.96/updater", exist_ok=True)
logging.basicConfig(
    filename=get_datadir() / "Blender/2.96/updater/AblerLauncher.log",
    format=LOG_FORMAT,
    level=logging.DEBUG,
    filemode="w",
)

logger = logging.getLogger()


def check_abler(dir_: str, installedversion: str) -> Tuple[Enum, Optional[list]]:
    """최신 릴리즈가 있는지 URL 주소로 확인"""

    finallist = None
    results = []
    state_ui = None

    # URL settings
    # Pre-Release 테스트 시에는 req = req[0]으로 pre-release 데이터 받아오기
    url = set_url()
    print(f"> url : {url}")

    is_release, req, state_ui = get_req_from_url(url, state_ui, dir_)
    if state_ui:
        return state_ui, finallist

    if not is_release:
        state_ui = StateUI.empty_repo
        return state_ui, finallist

    get_results_from_req(req, results)

    if results:
        if installedversion is None or installedversion == "":
            installedversion = "0.0.0"

        # ABLER 릴리즈 버전 > 설치 버전
        if StrictVersion(results[0]["version"]) > StrictVersion(installedversion):
            print(f"> New ABLER Ver. : {results[0]['version']}")
            state_ui = StateUI.update_abler
            finallist = results
            return state_ui, finallist

        # ABLER 릴리즈 버전 == 설치 버전
        else:
            state_ui = StateUI.execute

    # 통신 오류로 results가 없어서 바로 ABLER 실행
    else:
        state_ui = StateUI.execute

    return state_ui, finallist


def get_req_from_url(
    url: str, state_ui: Enum, dir_: str
) -> Tuple[bool, Optional[dict], Enum]:
    """깃헙 서버에서 url의 릴리즈 정보를 받아오는 함수"""

    # Do path settings save here, in case user has manually edited it
    config = configparser.ConfigParser()
    config.read(get_datadir() / "Blender/2.96/updater/config.ini")
    config.set("main", "path", dir_)
    with open(get_datadir() / "Blender/2.96/updater/config.ini", "w") as f:
        config.write(f)

    try:
        req = requests.get(url).json()
    except Exception as e:
        # self.statusBar().showMessage(
        #     "Error reaching server - check your internet connection"
        # )
        # logger.error(e)
        # self.frm_start.show()
        logger.error(e)
        state_ui = StateUI.error

    # Pre-Release에서는 req[0]이 pre-release 정보를 가지고 있음
    if pre_rel or new_repo_pre_rel:
        req = req[0]

    is_release = True
    try:
        is_release = req["message"] != "Not Found"
    except Exception as e:
        logger.debug("Release found")

    return is_release, req, state_ui


def get_results_from_req(req: dict, results: list) -> None:
    """req에서 필요한 info를 results에 추가"""

    for asset in req["assets"]:
        target = asset["browser_download_url"]
        filename = target.split("/")[-1]
        target_type = "Release"
        version_tag = req["name"][1:]

        if sys.platform == "win32":
            if "Windows" in target and "zip" in target and target_type in target:
                info = {
                    "url": target,
                    "os": "Windows",
                    "filename": filename,
                    "version": version_tag,
                    "arch": "x64",
                }
                results.append(info)

        elif sys.platform == "darwin":
            if os.system("sysctl -in sysctl.proc_translated") == 1:
                if (
                    "macOS" in target
                    and "zip" in target
                    and target_type in target
                    and "M1" in target
                ):
                    info = {
                        "url": target,
                        "os": "macOS",
                        "filename": filename,
                        "version": version_tag,
                        "arch": "arm64",
                    }
                    results.append(info)
            else:
                if (
                    "macOS" in target
                    and "zip" in target
                    and target_type in target
                    and "Intel" in target
                ):
                    info = {
                        "url": target,
                        "os": "macOS",
                        "filename": filename,
                        "version": version_tag,
                        "arch": "x86_64",
                    }
                    results.append(info)
