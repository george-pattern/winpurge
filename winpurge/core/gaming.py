"""
WinPurge Gaming Module
Handles gaming optimization and performance tweaks.
"""

import logging
from typing import Callable, Optional

from winpurge.utils import run_powershell, run_command, get_logger

logger = get_logger(__name__)


class GamingManager:
    """Manager for gaming optimization."""
    
    def apply_gaming_optimizations(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Apply comprehensive gaming optimizations.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            optimizations = [
                ("Enabling Game Mode", self.enable_game_mode),
                ("Disabling Game Bar overlay", self.disable_game_bar),
                ("Setting High Performance power plan", self.set_high_performance),
                ("Disabling Nagle's algorithm", self.disable_nagle),
                ("Disabling mouse acceleration", self.disable_mouse_acceleration),
                ("Disabling fullscreen optimizations", self.disable_fullscreen_optimizations)
            ]
            
            for description, method in optimizations:
                if progress_callback:
                    progress_callback(description)
                
                try:
                    method()
                except Exception as e:
                    logger.warning(f"Failed during {description}: {e}")
            
            logger.info("Gaming optimizations applied successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply gaming optimizations: {e}")
            return False
    
    def enable_game_mode(self) -> bool:
        """
        Enable Game Mode.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\Software\\Microsoft\\GameBar" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\GameBar" -Name "AllowAutoGameMode" -Value 1 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Game Mode enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable Game Mode: {e}")
            return False
    
    def disable_game_bar(self) -> bool:
        """
        Disable Game Bar overlay.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" -Name "AppCaptureEnabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\System\\GameConfigStore" -Name "GameDVR_Enabled" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Game Bar disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable Game Bar: {e}")
            return False
    
    def set_high_performance(self) -> bool:
        """
        Set power plan to High Performance.
        
        Returns:
            bool: True if successful.
        """
        try:
            # GUID for High Performance plan
            command = [
                "powercfg",
                "/setactive",
                "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
            ]
            
            code, stdout, stderr = run_command(command)
            
            if code == 0:
                logger.debug("High Performance power plan set")
                return True
            else:
                logger.warning(f"Failed to set power plan: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Failed to set high performance plan: {e}")
            return False
    
    def disable_nagle(self) -> bool:
        """
        Disable Nagle's algorithm for lower network latency.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            $interfaces = Get-NetAdapter | Where-Object {$_.Status -eq "Up"}
            foreach ($interface in $interfaces) {
                $reg_path = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\$($interface.InterfaceGuid)"
                New-Item -Path $reg_path -Force -ErrorAction SilentlyContinue | Out-Null
                Set-ItemProperty -Path $reg_path -Name "TcpAckFrequency" -Value 1 -ErrorAction SilentlyContinue
                Set-ItemProperty -Path $reg_path -Name "TCPNoDelay" -Value 1 -ErrorAction SilentlyContinue
            }
            """
            
            run_powershell(script)
            logger.debug("Nagle's algorithm disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable Nagle's algorithm: {e}")
            return False
    
    def disable_mouse_acceleration(self) -> bool:
        """
        Disable mouse acceleration.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\Control Panel\\Mouse" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\Control Panel\\Mouse" -Name "MouseSpeed" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\Control Panel\\Mouse" -Name "MouseThreshold1" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\Control Panel\\Mouse" -Name "MouseThreshold2" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Mouse acceleration disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable mouse acceleration: {e}")
            return False
    
    def disable_fullscreen_optimizations(self) -> bool:
        """
        Disable fullscreen optimizations.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\System\\GameConfigStore" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\System\\GameConfigStore" -Name "GameDVR_FSEBehaviorMode" -Value 2 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Fullscreen optimizations disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable fullscreen optimizations: {e}")
            return False
    
    def check_hags_status(self) -> bool:
        """
        Check if Hardware Accelerated GPU Scheduling is enabled.
        
        Returns:
            bool: True if HAGS is enabled, False otherwise.
        """
        try:
            script = """
            Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" -Name "HwSchMode" -ErrorAction SilentlyContinue
            """
            
            code, stdout, stderr = run_powershell(script, capture_output=True)
            
            if code == 0 and "1" in stdout:
                logger.debug("HAGS is enabled")
                return True
            else:
                logger.debug("HAGS is disabled or not available")
                return False
        except Exception as e:
            logger.error(f"Failed to check HAGS status: {e}")
            return False
