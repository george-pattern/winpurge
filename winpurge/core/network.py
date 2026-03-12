"""
WinPurge Network Module
Handles DNS configuration and network optimization.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any

from winpurge.constants import DATA_DIR
from winpurge.utils import run_command, run_powershell, get_logger

logger = get_logger(__name__)


class NetworkManager:
    """Manager for network configuration."""
    
    def __init__(self):
        """Initialize the network manager."""
        self.hosts_file = Path("C:\\Windows\\System32\\drivers\\etc\\hosts")
        self.telemetry_endpoints = self._load_telemetry_endpoints()
    
    def _load_telemetry_endpoints(self) -> List[Dict]:
        """
        Load telemetry endpoints to block.
        
        Returns:
            List of telemetry endpoint dictionaries.
        """
        try:
            endpoints_file = DATA_DIR / "telemetry_endpoints.json"
            with open(endpoints_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("telemetry_endpoints", [])
        except Exception as e:
            logger.error(f"Failed to load telemetry endpoints: {e}")
            return []
    
    def apply_dns_preset(self, dns_type: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        Apply a DNS preset configuration.
        
        Args:
            dns_type: Type of DNS ("cloudflare", "google", "adguard", "quad9").
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        dns_servers = {
            "cloudflare": ["1.1.1.1", "1.0.0.1"],
            "google": ["8.8.8.8", "8.8.4.4"],
            "adguard": ["94.140.14.14", "94.140.15.15"],
            "quad9": ["9.9.9.9", "149.112.112.112"]
        }
        
        servers = dns_servers.get(dns_type, [])
        
        if not servers:
            logger.error(f"Unknown DNS type: {dns_type}")
            return False
        
        try:
            if progress_callback:
                progress_callback(f"Configuring DNS to {dns_type}")
            
            # Get active network adapter
            script = f"""
            $adapter = Get-NetAdapter | Where-Object {{$_.Status -eq 'Up'}} | Select-Object -First 1
            if ($adapter) {{
                Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex `
                    -ServerAddresses @('{dns_servers[0]}', '{dns_servers[1]}') `
                    -ErrorAction SilentlyContinue
                Write-Output "DNS configured on $($adapter.Name)"
            }}
            """
            
            code, stdout, stderr = run_powershell(script, capture_output=True)
            
            if code == 0:
                logger.info(f"DNS configured to {dns_type}")
                return True
            else:
                logger.warning(f"Failed to configure DNS: {stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to apply DNS preset: {e}")
            return False
    
    def block_telemetry_domains(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        Add telemetry domains to hosts file.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            if progress_callback:
                progress_callback("Blocking telemetry domains...")
            
            # Read current hosts file
            try:
                with open(self.hosts_file, "r", encoding="utf-8") as f:
                    hosts_content = f.read()
            except FileNotFoundError:
                hosts_content = ""
            
            # Add telemetry domains
            new_entries = []
            for endpoint in self.telemetry_endpoints:
                domain = endpoint.get("domain", "")
                if domain and f"127.0.0.1\t{domain}" not in hosts_content:
                    new_entries.append(f"127.0.0.1\t{domain}")
            
            if new_entries:
                hosts_content += "\n# WinPurge Telemetry Blocking\n"
                hosts_content += "\n".join(new_entries) + "\n"
                
                # Write updated hosts file
                with open(self.hosts_file, "w", encoding="utf-8") as f:
                    f.write(hosts_content)
                
                logger.info(f"Added {len(new_entries)} telemetry domains to hosts file")
                return True
            else:
                logger.info("All telemetry domains already blocked")
                return True
        
        except Exception as e:
            logger.error(f"Failed to block telemetry domains: {e}")
            return False
    
    def edit_hosts_file(self, entries: List[dict], action: str = "add") -> bool:
        """
        Edit the hosts file by adding or removing entries.
        
        Args:
            entries: List of {ip, hostname} dictionaries.
            action: "add" or "remove".
        
        Returns:
            bool: True if successful.
        """
        try:
            # Read current hosts
            try:
                with open(self.hosts_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except FileNotFoundError:
                lines = []
            
            if action == "add":
                # Add entries
                for entry in entries:
                    ip = entry.get("ip", "")
                    hostname = entry.get("hostname", "")
                    new_line = f"{ip}\t{hostname}\n"
                    
                    if new_line not in lines:
                        lines.append(new_line)
            
            elif action == "remove":
                # Remove entries
                for entry in entries:
                    hostname = entry.get("hostname", "")
                    lines = [l for l in lines if hostname not in l]
            
            # Write back
            with open(self.hosts_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            
            logger.info(f"Hosts file updated: {action} {len(entries)} entries")
            return True
        
        except Exception as e:
            logger.error(f"Failed to edit hosts file: {e}")
            return False
    
    def get_hosts_file_entries(self) -> List[dict]:
        """
        Get current hosts file entries.
        
        Returns:
            List of {ip, hostname} dictionaries.
        """
        entries = []
        
        try:
            with open(self.hosts_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            entries.append({
                                "ip": parts[0],
                                "hostname": parts[1]
                            })
        except Exception as e:
            logger.error(f"Failed to read hosts file: {e}")
        
        return entries
    
    def optimize_network_adapter(self, progress_callback: Optional[Callable] = None) -> bool:
        """
        Optimize network adapter settings.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            if progress_callback:
                progress_callback("Optimizing network adapter...")
            
            script = """
            $adapters = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}
            foreach ($adapter in $adapters) {
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Large Send Offload Version 2 (IPv4)" -RegistryValue 0 -ErrorAction SilentlyContinue
                Set-NetAdapterAdvancedProperty -Name $adapter.Name -DisplayName "Receive Side Scaling" -RegistryValue 1 -ErrorAction SilentlyContinue
            }
            """
            
            code, stdout, stderr = run_powershell(script)
            
            if code == 0:
                logger.info("Network adapter optimized")
                return True
            else:
                logger.warning(f"Failed to optimize network adapter: {stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to optimize network adapter: {e}")
            return False
