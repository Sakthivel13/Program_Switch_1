;---------------------------------------
; Installer Name / Output / Settings
;---------------------------------------
OutFile "TVS_NIRIX_Setup.exe"
InstallDir "C:\Nirix\ApplicationFiles"
RequestExecutionLevel user
Icon "NIRIX App Logo.ico"

;---------------------------------------
; Pages
;---------------------------------------
Page directory
Page instfiles

;---------------------------------------
; INSTALL SECTION
;---------------------------------------
Section "Install TVS_NIRIX"

    SetOutPath "$INSTDIR"

    ; Copy main EXE
    File /r "dist\TVS_NIRIX\TVS_NIRIX.exe"

    ; Copy folders
    File /r "dist\TVS_NIRIX\sku_files"
    File /r "dist\TVS_NIRIX\Storage"
    File /r "dist\TVS_NIRIX\_internal"
    File /r "dist\TVS_NIRIX\Orbiter_RVS"
    File /r "dist\TVS_NIRIX\dll"
    File /r "dist\TVS_NIRIX\dtc error code"

    ; Config files
    File "dist\TVS_NIRIX\station.ini"
    File "dist\TVS_NIRIX\api.ini"
    File "dist\TVS_NIRIX\log_cleanup.py"
    File "dist\TVS_NIRIX\scanner.ini"
    File "dist\TVS_NIRIX\SKU_File_Mapping.xlsx"

    ; UI Assets
    File "dist\TVS_NIRIX\fail picture.png"
    File "dist\TVS_NIRIX\Pass picture.png"
    File "dist\TVS_NIRIX\NIRIX Logo.png"
    File "dist\TVS_NIRIX\NIRIX_Logo.png"
    File "dist\TVS_NIRIX\TVS logo white.png"
    File "dist\TVS_NIRIX\NIRIX App Logo.ico"

    ;---------------------------------------
    ; Shortcuts (Direct EXE launch)
    ;---------------------------------------
    CreateShortcut "$DESKTOP\TVS_NIRIX.lnk" "$INSTDIR\TVS_NIRIX.exe" "" "$INSTDIR\NIRIX App Logo.ico"
    CreateShortcut "$SMPROGRAMS\TVS_NIRIX.lnk" "$INSTDIR\TVS_NIRIX.exe" "" "$INSTDIR\NIRIX App Logo.ico"

SectionEnd

;---------------------------------------
; UNINSTALL
;---------------------------------------
Section "Uninstall"
    Delete "$DESKTOP\TVS_NIRIX.lnk"
    Delete "$SMPROGRAMS\TVS_NIRIX.lnk"
    RMDir /r "$INSTDIR"
SectionEnd
