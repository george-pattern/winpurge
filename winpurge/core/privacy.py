"""
WinPurge Privacy Module
Handles Windows privacy hardening and data collection disabling.
"""

import logging
from typing import Callable, Optional

from winpurge.utils import run_powershell, get_logger

logger = get_logger(__name__)


class PrivacyManager:
    """Manager for privacy hardening."""
    
    def apply_privacy_hardening(
        self,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Apply comprehensive privacy hardening settings.
        
        Args:
            progress_callback: Optional callback for progress updates.
        
        Returns:
            bool: True if successful.
        """
        try:
            settings = [
                ("Disabling clipboard history sync", self.disable_clipboard_sync),
                ("Removing Start Menu ads", self.disable_start_menu_ads),
                ("Removing lock screen ads", self.disable_lockscreen_ads),
                ("Disabling web activity tracking", self.disable_web_activity),
                ("Disabling advertising ID", self.disable_advertising_id),
                ("Disabling tailored experiences", self.disable_tailored_experiences),
                ("Disabling diagnostic data", self.disable_diagnostics),
                ("Disabling activity feed", self.disable_activity_feed),
                ("Disabling app suggestions", self.disable_app_suggestions)
            ]
            
            for description, method in settings:
                if progress_callback:
                    progress_callback(description)
                
                try:
                    method()
                except Exception as e:
                    logger.warning(f"Failed during {description}: {e}")
            
            logger.info("Privacy hardening applied successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to apply privacy hardening: {e}")
            return False
    
    def disable_clipboard_sync(self) -> bool:
        """
        Disable clipboard history synchronization.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "AllowClipboardHistory" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "AllowCrossDeviceClipboard" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Clipboard sync disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable clipboard sync: {e}")
            return False
    
    def disable_start_menu_ads(self) -> bool:
        """
        Disable Start Menu ads and suggestions.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "SubscribedContent-338388Enabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "SubscribedContent-338389Enabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "SubscribedContent-353694Enabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "SubscribedContent-353696Enabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "SystemPaneSuggestionsEnabled" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Start Menu ads disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable Start Menu ads: {e}")
            return False
    
    def disable_lockscreen_ads(self) -> bool:
        """
        Disable lock screen ads and spotlight.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "RotatingLockScreenEnabled" -Value 0 -ErrorAction SilentlyContinue
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "RotatingLockScreenOverlayEnabled" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Lock screen ads disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable lock screen ads: {e}")
            return False
    
    def disable_web_activity(self) -> bool:
        """
        Disable web/browse activity tracking.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Privacy" -Name "TailoredExperiencesAllowed" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Web activity tracking disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable web activity tracking: {e}")
            return False
    
    def disable_advertising_id(self) -> bool:
        """
        Disable advertising ID.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" -Name "Enabled" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Advertising ID disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable advertising ID: {e}")
            return False
    
    def disable_tailored_experiences(self) -> bool:
        """
        Disable tailored experiences and ads.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "ContentDeliveryAllowed" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Tailored experiences disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable tailored experiences: {e}")
            return False
    
    def disable_diagnostics(self) -> bool:
        """
        Minimize diagnostic data collection.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" -Name "AllowTelemetry" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Diagnostic data collection minimized")
            return True
        except Exception as e:
            logger.error(f"Failed to disable diagnostics: {e}")
            return False
    
    def disable_activity_feed(self) -> bool:
        """
        Disable activity feed.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" -Name "ShowRecentlyUsedFiles" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("Activity feed disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable activity feed: {e}")
            return False
    
    def disable_app_suggestions(self) -> bool:
        """
        Disable app suggestions.
        
        Returns:
            bool: True if successful.
        """
        try:
            script = """
            New-Item -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Force -ErrorAction SilentlyContinue | Out-Null
            Set-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" -Name "AppsSilentInstall" -Value 0 -ErrorAction SilentlyContinue
            """
            
            run_powershell(script)
            logger.debug("App suggestions disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable app suggestions: {e}")
            return False
