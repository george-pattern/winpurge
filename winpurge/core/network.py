import json
from typing import Callable, Dict, List, Optional, Tuple

from winpurge.constants import DNS_PRESETS, HOSTS_FILE
from winpurge.utils import logger, run_command, run_powershell


class NetworkManager:
    def get_current_dns(self) -> Dict[str, str]:
        dns_config: Dict[str, str] = {}
        try:
            success, output = run_powershell(
                "Get-DnsClientServerAddress -AddressFamily IPv4 | "
                "Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json -Depth 4"
            )
            if not success or not output:
                return dns_config

            interfaces = json.loads(output)
            if isinstance(interfaces, dict):
                interfaces = [interfaces]
            if not isinstance(interfaces, list):
                return dns_config

            for iface in interfaces:
                if not isinstance(iface, dict):
                    continue
                alias = str(iface.get("InterfaceAlias", "")).strip()
                servers = iface.get("ServerAddresses", [])
                if not alias:
                    continue
                if isinstance(servers, list) and servers:
                    dns_config[alias] = ", ".join(str(x) for x in servers if str(x).strip())
                elif servers:
                    dns_config[alias] = str(servers)
        except Exception as e:
            logger.error(f"Failed to get DNS configuration: {e}")
        return dns_config

    def get_network_interfaces(self) -> List[str]:
        interfaces: List[str] = []
        try:
            success, output = run_powershell(
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -ExpandProperty Name"
            )
            if success and output:
                interfaces = [line.strip() for line in output.splitlines() if line.strip()]
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
        return interfaces

    def set_dns(
        self,
        interface: str,
        primary: str,
        secondary: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback(f"Setting DNS for {interface}...")

            success, output = run_command([
                "netsh", "interface", "ip", "set", "dns", f"name={interface}", "static", primary
            ])
            if not success:
                return False, f"Failed to set primary DNS: {output}"

            if secondary:
                success, output = run_command([
                    "netsh", "interface", "ip", "add", "dns", f"name={interface}", secondary, "index=2"
                ])
                if not success:
                    return False, f"Failed to set secondary DNS: {output}"

            run_command(["ipconfig", "/flushdns"])
            logger.info(f"DNS set for {interface}: {primary}, {secondary}")
            return True, f"DNS configured successfully for {interface}"
        except Exception as e:
            logger.error(f"Failed to set DNS: {e}")
            return False, f"Failed to set DNS: {e}"

    def set_dns_preset(
        self,
        preset_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        preset = DNS_PRESETS.get(preset_name)
        if not preset:
            return False, f"Unknown DNS preset: {preset_name}"

        interfaces = self.get_network_interfaces()
        if not interfaces:
            return False, "No active network interfaces found"

        errors: List[str] = []
        for interface in interfaces:
            success, message = self.set_dns(
                interface,
                str(preset["primary"]),
                str(preset.get("secondary", "")),
                progress_callback,
            )
            if not success:
                errors.append(f"{interface}: {message}")

        if errors:
            return True, f"DNS set with warnings: {'; '.join(errors)}"
        return True, f"{preset['name']} DNS configured for all interfaces"

    def reset_dns(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            interfaces = self.get_network_interfaces()
            if not interfaces:
                return False, "No active network interfaces found"

            errors: List[str] = []
            for interface in interfaces:
                if progress_callback:
                    progress_callback(f"Resetting DNS for {interface}...")
                success, output = run_command([
                    "netsh", "interface", "ip", "set", "dns", f"name={interface}", "dhcp"
                ])
                if not success:
                    errors.append(f"{interface}: {output}")

            run_command(["ipconfig", "/flushdns"])

            if errors:
                return True, f"DNS reset with warnings: {'; '.join(errors)}"

            logger.info("DNS reset to DHCP")
            return True, "DNS reset to automatic for all interfaces"
        except Exception as e:
            logger.error(f"Failed to reset DNS: {e}")
            return False, f"Failed to reset DNS: {e}"

    def get_hosts_file_content(self) -> str:
        try:
            if HOSTS_FILE.exists():
                return HOSTS_FILE.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to read hosts file: {e}")
        return ""

    def get_hosts_entry_count(self) -> int:
        content = self.get_hosts_file_content()
        count = 0
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            low = stripped.lower()
            if low.startswith("127.0.0.1 localhost") or low.startswith("::1 localhost"):
                continue
            count += 1
        return count

    def add_hosts_entries(
        self,
        entries: List[str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Updating hosts file...")

            current_content = self.get_hosts_file_content()
            normalized_existing = {line.strip() for line in current_content.splitlines() if line.strip()}
            new_entries = [entry.strip() for entry in entries if entry.strip() and entry.strip() not in normalized_existing]

            if not new_entries:
                return True, "All entries already exist in hosts file"

            content = current_content.rstrip()
            if content:
                content += "\n\n"
            content += "\n".join(new_entries) + "\n"

            HOSTS_FILE.write_text(content, encoding="utf-8")
            run_command(["ipconfig", "/flushdns"])
            logger.info(f"Added {len(new_entries)} entries to hosts file")
            return True, f"Added {len(new_entries)} entries to hosts file"
        except PermissionError:
            return False, "Permission denied. Run as administrator."
        except Exception as e:
            logger.error(f"Failed to add hosts entries: {e}")
            return False, f"Failed to add hosts entries: {e}"

    def save_hosts_file(
        self,
        content: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Saving hosts file...")
            HOSTS_FILE.write_text(content, encoding="utf-8")
            run_command(["ipconfig", "/flushdns"])
            logger.info("Hosts file saved")
            return True, "Hosts file saved successfully"
        except PermissionError:
            return False, "Permission denied. Run as administrator."
        except Exception as e:
            logger.error(f"Failed to save hosts file: {e}")
            return False, f"Failed to save hosts file: {e}"

    def disable_large_send_offload(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Disabling Large Send Offload...")
            success, output = run_powershell(
                "Get-NetAdapterAdvancedProperty | "
                "Where-Object {$_.DisplayName -like '*Large Send Offload*'} | "
                "ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name -DisplayName $_.DisplayName -DisplayValue 'Disabled' }"
            )
            if success:
                logger.info("Large Send Offload disabled")
                return True, "Large Send Offload disabled"
            return False, output or "Failed to disable Large Send Offload"
        except Exception as e:
            logger.error(f"Failed to disable Large Send Offload: {e}")
            return False, f"Failed to disable Large Send Offload: {e}"

    def enable_receive_side_scaling(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        try:
            if progress_callback:
                progress_callback("Enabling Receive Side Scaling...")
            success, output = run_powershell(
                "Get-NetAdapterAdvancedProperty | "
                "Where-Object {$_.DisplayName -like '*Receive Side Scaling*'} | "
                "ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name -DisplayName $_.DisplayName -DisplayValue 'Enabled' }"
            )
            if success:
                logger.info("Receive Side Scaling enabled")
                return True, "Receive Side Scaling enabled"
            return False, output or "Failed to enable Receive Side Scaling"
        except Exception as e:
            logger.error(f"Failed to enable Receive Side Scaling: {e}")
            return False, f"Failed to enable Receive Side Scaling: {e}"


network_manager = NetworkManager()