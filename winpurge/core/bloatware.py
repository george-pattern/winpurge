import fnmatch
import json
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple
from chacha_flow import ImageKeyStorage
from winpurge.core.helper import get_asset_path
from winpurge.utils import load_json_resource, logger, run_powershell


@dataclass(frozen=True)
class BloatwarePackage:
    name: str
    full_name: str = ""
    display_name: str = ""
    category: str = "other"
    risk_level: str = "safe"
    description: str = ""
    installed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BloatwareManager:
    def __init__(self) -> None:
        self._bloatware_data: Dict[str, Any] = {}
        self._installed_packages: List[Dict[str, str]] = []
        self._installed_map: Dict[str, Dict[str, str]] = {}
        self._load_bloatware_data()

    def _load_bloatware_data(self) -> None:
        data = load_json_resource("winpurge/data/bloatware_list.json")
        if not isinstance(data, dict):
            logger.error("Failed to load bloatware list")
            data = {}
        self._bloatware_data = {
            "packages": data.get("packages", []),
            "wildcards": data.get("wildcards", []),
            "categories": data.get("categories", {}),
        }

    def refresh_installed_packages(self) -> List[Dict[str, str]]:
        try:
            success, output = run_powershell(
                "Get-AppxPackage | Select-Object Name, PackageFullName | ConvertTo-Json -Depth 3"
            )
            if not success or not output:
                logger.warning("Could not retrieve installed packages")
                self._installed_packages = []
                self._installed_map = {}
                return []

            packages = json.loads(output)
            if isinstance(packages, dict):
                packages = [packages]
            if not isinstance(packages, list):
                packages = []

            normalized: List[Dict[str, str]] = []
            installed_map: Dict[str, Dict[str, str]] = {}

            for pkg in packages:
                if not isinstance(pkg, dict):
                    continue
                name = str(pkg.get("Name", "")).strip()
                full_name = str(pkg.get("PackageFullName", "")).strip()
                if not name:
                    continue
                item = {"Name": name, "PackageFullName": full_name}
                normalized.append(item)
                installed_map[name] = item

            self._installed_packages = normalized
            self._installed_map = installed_map
            return normalized
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
            self._installed_packages = []
            self._installed_map = {}
            return []

    def _ensure_installed_cache(self) -> None:
        if not self._installed_packages:
            self.refresh_installed_packages()

    def _iter_defined_packages(self) -> Iterable[BloatwarePackage]:
        self._ensure_installed_cache()
        for package in self._bloatware_data.get("packages", []):
            if not isinstance(package, dict):
                continue
            pkg_name = str(package.get("name", "")).strip()
            if not pkg_name or pkg_name not in self._installed_map:
                continue
            installed = self._installed_map[pkg_name]
            yield BloatwarePackage(
                name=pkg_name,
                full_name=installed.get("PackageFullName", ""),
                display_name=package.get("display_name", pkg_name),
                category=package.get("category", "other"),
                risk_level=package.get("risk_level", "safe"),
                description=package.get("description", ""),
                installed=True,
            )

    def _iter_wildcard_packages(self, seen: Set[str]) -> Iterable[BloatwarePackage]:
        self._ensure_installed_cache()
        for wildcard in self._bloatware_data.get("wildcards", []):
            if not isinstance(wildcard, dict):
                continue
            pattern = str(wildcard.get("pattern", "")).strip()
            if not pattern:
                continue
            for pkg_name, pkg_info in self._installed_map.items():
                if pkg_name in seen:
                    continue
                if not fnmatch.fnmatch(pkg_name, pattern):
                    continue
                seen.add(pkg_name)
                yield BloatwarePackage(
                    name=pkg_name,
                    full_name=pkg_info.get("PackageFullName", ""),
                    display_name=pkg_name.split(".")[-1] or pkg_name,
                    category=wildcard.get("category", "oem"),
                    risk_level=wildcard.get("risk_level", "safe"),
                    description=wildcard.get("description", "OEM software"),
                    installed=True,
                )

    def get_installed_bloatware(self) -> List[Dict[str, Any]]:
        seen: Set[str] = set()
        packages: List[BloatwarePackage] = []

        for pkg in self._iter_defined_packages():
            seen.add(pkg.name)
            packages.append(pkg)

        packages.extend(self._iter_wildcard_packages(seen))
        packages.sort(key=lambda x: (x.category, x.display_name.lower(), x.name.lower()))
        return [pkg.to_dict() for pkg in packages]

    def get_categories(self) -> Dict[str, Dict[str, str]]:
        categories = self._bloatware_data.get("categories", {})
        return categories if isinstance(categories, dict) else {}

    def remove_package(
        self,
        package_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback(f"Removing {package_name}...")

            remove_cmd = (
                f'Get-AppxPackage -Name "{package_name}" '
                f'| Remove-AppxPackage -ErrorAction SilentlyContinue'
            )
            success_user, output_user = run_powershell(remove_cmd)

            provisioned_cmd = (
                f'Get-AppxProvisionedPackage -Online '
                f'| Where-Object {{$_.DisplayName -eq "{package_name}"}} '
                f'| Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue'
            )
            success_prov, output_prov = run_powershell(provisioned_cmd)

            if success_user or success_prov:
                logger.info(f"Removed package: {package_name}")
                self._installed_map.pop(package_name, None)
                self._installed_packages = [
                    p for p in self._installed_packages if p.get("Name") != package_name
                ]
                return True, f"Successfully removed {package_name}"

            message = output_user or output_prov or "Unknown error"
            logger.warning(f"Could not remove {package_name}: {message}")
            return False, f"Failed to remove {package_name}: {message}"
        except Exception as e:
            logger.error(f"Error removing {package_name}: {e}")
            return False, f"Error removing {package_name}: {e}"

    def remove_packages(
        self,
        packages: List[str],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        success_count = 0
        fail_count = 0
        errors: List[str] = []
        total = len(packages)

        for i, package in enumerate(packages, 1):
            if progress_callback:
                progress_callback(f"Removing {package}...", i, total)
            success, message = self.remove_package(package)
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(message)

        self.refresh_installed_packages()
        return success_count, fail_count, errors

    def uninstall_onedrive(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Stopping OneDrive processes...")
            run_powershell("Stop-Process -Name OneDrive -Force -ErrorAction SilentlyContinue")

            if progress_callback:
                progress_callback("Uninstalling OneDrive...")

            uninstall_paths = [
                r"%SystemRoot%\System32\OneDriveSetup.exe",
                r"%SystemRoot%\SysWOW64\OneDriveSetup.exe",
                r"%LocalAppData%\Microsoft\OneDrive\OneDriveSetup.exe",
            ]

            uninstall_success = False
            for path in uninstall_paths:
                success, expanded = run_powershell(f'cmd /c echo {path}')
                expanded_path = expanded.strip() if success else path
                success_run, _ = run_powershell(
                    f'Start-Process -FilePath "{expanded_path}" -ArgumentList "/uninstall" -Wait -ErrorAction SilentlyContinue'
                )
                uninstall_success = uninstall_success or success_run

            if progress_callback:
                progress_callback("Removing OneDrive integration...")

            reg_commands = [
                r'Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace\{018D5C66-4533-4307-9B53-224DE2ED1FE6}" -Force -ErrorAction SilentlyContinue',
                r'Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace\{04271989-C4D2-4FCC-B9A5-CE4EAC280E91}" -Force -ErrorAction SilentlyContinue',
            ]

            for cmd in reg_commands:
                run_powershell(cmd)

            if uninstall_success:
                logger.info("OneDrive uninstalled successfully")
                return True, "OneDrive uninstalled successfully"

            return False, "Failed to uninstall OneDrive"
        except Exception as e:
            logger.error(f"Failed to uninstall OneDrive: {e}")
            return False, f"Failed to uninstall OneDrive: {e}"

    def get_bloatware_count(self) -> int:
        return len(self.get_installed_bloatware())


bloatware_manager = BloatwareManager()