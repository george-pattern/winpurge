"""
WinPurge Network Module
Handles network configuration and optimization.
"""

import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple

from winpurge.constants import DNS_PRESETS, HOSTS_FILE
from winpurge.utils import logger, run_command, run_powershell


class NetworkManager:
    """Manages network configuration and optimizations."""
    
    def __init__(self) -> None:
        """Initialize the network manager."""
        pass
    
    def get_current_dns(self) -> Dict[str, str]:
        """
        Get current DNS configuration.
        
        Returns:
            Dictionary with interface names and their DNS servers.
        """
        dns_config = {}
        
        try:
            success, output = run_powershell(
                "Get-DnsClientServerAddress -AddressFamily IPv4 | "
                "Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json"
            )
            
            if success and output:
                import json
                interfaces = json.loads(output)
                
                if isinstance(interfaces, dict):
                    interfaces = [interfaces]
                
                for iface in interfaces:
                    alias = iface.get("InterfaceAlias", "")
                    servers = iface.get("ServerAddresses", [])
                    
                    if alias and servers:
                        dns_config[alias] = ", ".join(servers) if isinstance(servers, list) else str(servers)
                        
        except Exception as e:
            logger.error(f"Failed to get DNS configuration: {e}")
        
        return dns_config
    
    def get_network_interfaces(self) -> List[str]:
        """
        Get list of active network interfaces.
        
        Returns:
            List of interface names.
        """
        interfaces = []
        
        try:
            success, output = run_powershell(
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
                "Select-Object -ExpandProperty Name"
            )
            
            if success and output:
                interfaces = [line.strip() for line in output.split("\n") if line.strip()]
                
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
        """
        Set DNS servers for an interface.
        
        Args:
            interface: Network interface name.
            primary: Primary DNS server.
            secondary: Secondary DNS server.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback(f"Setting DNS for {interface}...")
            
            # Set primary DNS
            success, output = run_command([
                "netsh", "interface", "ip", "set", "dns",
                f"name={interface}", "static", primary
            ])
            
            if not success:
                return False, f"Failed to set primary DNS: {output}"
            
            # Set secondary DNS if provided
            if secondary:
                success, output = run_command([
                    "netsh", "interface", "ip", "add", "dns",
                    f"name={interface}", secondary, "index=2"
                ])
            
            # Flush DNS cache
            run_command(["ipconfig", "/flushdns"])
            
            logger.info(f"DNS set for {interface}: {primary}, {secondary}")
            return True, f"DNS configured successfully for {interface}"
            
        except Exception as e:
            logger.error(f"Failed to set DNS: {e}")
            return False, f"Failed to set DNS: {str(e)}"
    
    def set_dns_preset(
        self,
        preset_name: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Apply a DNS preset to all active interfaces.
        
        Args:
            preset_name: Name of the DNS preset.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        preset = DNS_PRESETS.get(preset_name)
        if not preset:
            return False, f"Unknown DNS preset: {preset_name}"
        
        interfaces = self.get_network_interfaces()
        if not interfaces:
            return False, "No active network interfaces found"
        
        errors = []
        
        for interface in interfaces:
            success, message = self.set_dns(
                interface,
                preset["primary"],
                preset.get("secondary", ""),
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
        """
        Reset DNS to automatic (DHCP).
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            interfaces = self.get_network_interfaces()
            
            for interface in interfaces:
                if progress_callback:
                    progress_callback(f"Resetting DNS for {interface}...")
                
                run_command([
                    "netsh", "interface", "ip", "set", "dns",
                    f"name={interface}", "dhcp"
                ])
            
            run_command(["ipconfig", "/flushdns"])
            
            logger.info("DNS reset to DHCP")
            return True, "DNS reset to automatic for all interfaces"
            
        except Exception as e:
            logger.error(f"Failed to reset DNS: {e}")
            return False, f"Failed to reset DNS: {str(e)}"
    
    def get_hosts_file_content(self) -> str:
        """
        Read the current hosts file content.
        
        Returns:
            Hosts file content as string.
        """
        try:
            if HOSTS_FILE.exists():
                return HOSTS_FILE.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Failed to read hosts file: {e}")
        return ""
    
    def get_hosts_entry_count(self) -> int:
        """
        Get count of custom entries in hosts file.
        
        Returns:
            Number of non-comment entries.
        """
        content = self.get_hosts_file_content()
        count = 0
        
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("127.0.0.1 localhost"):
                count += 1
        
        return count
    
    def add_hosts_entries(
        self,
        entries: List[str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Add entries to the hosts file.
        
        Args:
            entries: List of entries (format: "0.0.0.0 domain.com").
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Updating hosts file...")
            
            current_content = self.get_hosts_file_content()
            new_entries = []
            
            for entry in entries:
                if entry not in current_content:
                    new_entries.append(entry)
            
            if new_entries:
                new_content = current_content.rstrip() + "\n\n" + "\n".join(new_entries) + "\n"
                HOSTS_FILE.write_text(new_content, encoding="utf-8")
                
                run_command(["ipconfig", "/flushdns"])
                
                logger.info(f"Added {len(new_entries)} entries to hosts file")
                return True, f"Added {len(new_entries)} entries to hosts file"
            else:
                return True, "All entries already exist in hosts file"
                
        except PermissionError:
            return False, "Permission denied. Run as administrator."
        except Exception as e:
            logger.error(f"Failed to add hosts entries: {e}")
            return False, f"Failed to add hosts entries: {str(e)}"
    
    def save_hosts_file(
        self,
        content: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Save content to the hosts file.
        
        Args:
            content: New hosts file content.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
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
            return False, f"Failed to save hosts file: {str(e)}"
    
    def disable_large_send_offload(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Disable Large Send Offload for better network performance.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Disabling Large Send Offload...")
            
            success, output = run_powershell(
                "Get-NetAdapterAdvancedProperty | "
                "Where-Object {$_.DisplayName -like '*Large Send Offload*'} | "
                "ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name "
                "-DisplayName $_.DisplayName -DisplayValue 'Disabled' }"
            )
            
            logger.info("Large Send Offload disabled")
            return True, "Large Send Offload disabled"
            
        except Exception as e:
            logger.error(f"Failed to disable Large Send Offload: {e}")
            return False, f"Failed to disable Large Send Offload: {str(e)}"
    
    def enable_receive_side_scaling(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """
        Enable Receive Side Scaling for better network performance.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success, message).
        """
        try:
            if progress_callback:
                progress_callback("Enabling Receive Side Scaling...")
            
            success, output = run_powershell(
                "Get-NetAdapterAdvancedProperty | "
                "Where-Object {$_.DisplayName -like '*Receive Side Scaling*'} | "
                "ForEach-Object { Set-NetAdapterAdvancedProperty -Name $_.Name "
                "-DisplayName $_.DisplayName -DisplayValue 'Enabled' }"
            )
            
            logger.info("Receive Side Scaling enabled")
            return True, "Receive Side Scaling enabled"
            
        except Exception as e:
            logger.error(f"Failed to enable Receive Side Scaling: {e}")
            return False, f"Failed to enable Receive Side Scaling: {str(e)}"


network_manager = NetworkManager()