#!/usr/bin/env python3
#coding:utf8


# *** TROUBLESHOOTING ***
# 1) If you get the error "ImportError: No module named zope.interface" then add an empty __init__.py file to the PYTHONDIR/Lib/site-packages/zope directory
# 2) It is expected that you will have NSIS 3 NSIS from http://nsis.sourceforge.net installed.

import codecs
import sys
# try:
#     if (sys.version_info.major != 2) or (sys.version_info.minor < 7):
#         raise Exception("You must build Syncplay with Python 2.7!")
# except AttributeError:
#     import warnings
#     warnings.warn("You must build Syncplay with Python 2.7!")

from glob import glob
import os
import subprocess
from string import Template

from distutils.core import setup
try:
    from py2exe.build_exe import py2exe
except ImportError:
    from py2exe.distutils_buildexe import py2exe

import syncplay
from syncplay.messages import getMissingStrings, getMessage, getLanguages

missingStrings = getMissingStrings()
if missingStrings is not None and missingStrings != "":
    import warnings
    warnings.warn("MISSING/UNUSED STRINGS DETECTED:\n{}".format(missingStrings))

def get_nsis_path():
    bin_name = "makensis.exe"
    from winreg import HKEY_LOCAL_MACHINE as HKLM
    from winreg import KEY_READ, KEY_WOW64_32KEY, OpenKey, QueryValueEx

    try:
        nsisreg = OpenKey(HKLM, "Software\\NSIS", 0, KEY_READ | KEY_WOW64_32KEY)
        if QueryValueEx(nsisreg, "VersionMajor")[0] >= 3:
            return "{}\\{}".format(QueryValueEx(nsisreg, "")[0], bin_name)
        else:
            raise Exception("You must install NSIS 3 or later.")
    except WindowsError:
        return bin_name

NSIS_COMPILE = get_nsis_path()

OUT_DIR = "syncplay_v{}".format(syncplay.version)
SETUP_SCRIPT_PATH = "syncplay_setup.nsi"

languages = getLanguages()

def getLangTagFromNLF(lang):
    return "LANG_" + getMessage("installer-language-file", lang).upper().replace(".NLF","").replace("_","")


# Load languages
loadLanguageFileString = ""
for lang in languages:
    lineToAdd = "LoadLanguageFile \"$${{NSISDIR}}\\Contrib\\Language files\\{}\"".format(getMessage("installer-language-file", lang))
    loadLanguageFileString = loadLanguageFileString + "\r\n" + lineToAdd

# Add Version Keys
versionKeysString = ""
for lang in languages:
    languageIdent = getLangTagFromNLF(lang)
    lineToAdd = r"""  VIAddVersionKey /LANG=$${LANG_IDENT} "ProductName" "Syncplay"
  VIAddVersionKey /LANG=$${LANG_IDENT} "FileVersion" "$version.0"
  VIAddVersionKey /LANG=$${LANG_IDENT} "LegalCopyright" "Syncplay"
  VIAddVersionKey /LANG=$${LANG_IDENT} "FileDescription" "Syncplay"
  """.replace("LANG_IDENT", languageIdent)
    versionKeysString = versionKeysString + "\r\n" + lineToAdd

# Add Language Strings
languageString = ""
for lang in languages:
    languageIdent = getLangTagFromNLF(lang)

    # dict_dict = {'dict1':dict1, 'dicta':dicta, 'dict666':dict666}
    #
    # for name,dict_ in dict_dict.items():
    #     print 'the name of the dictionary is ', name
    #     print 'the dictionary looks like ', dict_

    langStringDict = {
        # "[NSIS key name]": "[messages_*.py key name]"
        "SyncplayLanguage": "LANGUAGE-TAG",
        "Associate": "installer-associate",
        "Shortcut": "installer-shortcut",
        "StartMenu": "installer-start-menu",
        "Desktop": "installer-desktop",
        "QuickLaunchBar": "installer-quick-launch-bar",
        "AutomaticUpdates": "installer-automatic-updates",
        "UninstConfig": "installer-uninstall-configuration"
    }
    for nsisKey, messageKey in langStringDict.items():
        nsisValue = getMessage(messageKey, lang)
        lineToAdd = "  LangString ^" + nsisKey + " $${" + languageIdent + "} \"" + nsisValue + "\""
        languageString = languageString + "\r\n" + lineToAdd
    languageString = languageString + "\r\n"

# Add Language Pushs
languagePushString = ""
for lang in languages:
    languageIdent = getLangTagFromNLF(lang)
    languagePushString = languagePushString + "Push $${" + languageIdent + "}\r\n"
    languagePushString = languagePushString + "Push '" + getMessage("LANGUAGE", lang) + "'\r\n"

NSIS_SCRIPT_TEMPLATE = r"""
  !include LogicLib.nsh
  !include nsDialogs.nsh
  !include FileFunc.nsh

""" + loadLanguageFileString + r"""
 
  Unicode true

  Name "Syncplay $version"
  OutFile "Syncplay-$version-Setup.exe"
  InstallDir $$PROGRAMFILES\Syncplay
  RequestExecutionLevel admin
  ManifestDPIAware true
  XPStyle on
  Icon syncplay\resources\icon.ico ;Change DIR
  SetCompressor /SOLID lzma

  VIProductVersion "$version.0"
  
  """ + versionKeysString + languageString + r"""
  ; Remove text to save space
  LangString ^ClickInstall $${LANG_GERMAN} " "

  PageEx license
    LicenseData syncplay\resources\license.rtf
  PageExEnd
  Page custom DirectoryCustom DirectoryCustomLeave
  Page instFiles

  UninstPage custom un.installConfirm un.installConfirmLeave
  UninstPage instFiles

  Var Dialog
  Var Icon_Syncplay
  Var Icon_Syncplay_Handle
  ;Var CheckBox_Associate
  Var CheckBox_AutomaticUpdates
  Var CheckBox_StartMenuShortcut
  Var CheckBox_DesktopShortcut
  Var CheckBox_QuickLaunchShortcut
  ;Var CheckBox_Associate_State
  Var CheckBox_AutomaticUpdates_State
  Var CheckBox_StartMenuShortcut_State
  Var CheckBox_DesktopShortcut_State
  Var CheckBox_QuickLaunchShortcut_State
  Var Button_Browse
  Var Directory
  Var GroupBox_DirSub
  Var Label_Text
  Var Label_Shortcut
  Var Label_Size
  Var Label_Space
  Var Text_Directory

  Var Uninst_Dialog
  Var Uninst_Icon
  Var Uninst_Icon_Handle
  Var Uninst_Label_Directory
  Var Uninst_Label_Text
  Var Uninst_Text_Directory
  Var Uninst_CheckBox_Config
  Var Uninst_CheckBox_Config_State

  Var Size
  Var SizeHex
  Var AvailibleSpace
  Var AvailibleSpaceGiB
  Var Drive
  Var VLC_Directory

  ;!macro APP_ASSOCIATE EXT FileCLASS DESCRIPTION COMMANDTEXT COMMAND
  ;  WriteRegStr HKCR ".$${EXT}" "" "$${FileCLASS}"
  ;  WriteRegStr HKCR "$${FileCLASS}" "" `$${DESCRIPTION}`
  ;  WriteRegStr HKCR "$${FileCLASS}\shell" "" "open"
  ;  WriteRegStr HKCR "$${FileCLASS}\shell\open" "" `$${COMMANDTEXT}`
  ;  WriteRegStr HKCR "$${FileCLASS}\shell\open\command" "" `$${COMMAND}`
  ;!macroend

  !macro APP_UNASSOCIATE EXT FileCLASS
    ; Backup the previously associated File class
    ReadRegStr $$R0 HKCR ".$${EXT}" `$${FileCLASS}_backup`
    WriteRegStr HKCR ".$${EXT}" "" "$$R0"
    DeleteRegKey HKCR `$${FileCLASS}`
  !macroend

  ;!macro ASSOCIATE EXT
  ;  !insertmacro APP_ASSOCIATE "$${EXT}" "Syncplay.$${EXT}" "$$INSTDIR\Syncplay.exe,%1%" \
  ;  "Open with Syncplay" "$$INSTDIR\Syncplay.exe $$\"%1$$\""
  ;!macroend

  !macro UNASSOCIATE EXT
    !insertmacro APP_UNASSOCIATE "$${EXT}" "Syncplay.$${EXT}"
  !macroend

  ;Prevents from running more than one instance of installer and sets default state of checkboxes
  Function .onInit
    System::Call 'kernel32::CreateMutexA(i 0, i 0, t "SyncplayMutex") i .r1 ?e'
    Pop $$R0
    StrCmp $$R0 0 +3
    MessageBox MB_OK|MB_ICONEXCLAMATION "The installer is already running."
      Abort

    ;StrCpy $$CheckBox_Associate_State $${BST_CHECKED}
    StrCpy $$CheckBox_StartMenuShortcut_State $${BST_CHECKED}

    Call GetSize
    Call DriveSpace

    $${GetParameters} $$0
    ClearErrors
    $${GetOptions} $$0 "/LANG=" $$0
    $${IfNot} $${Errors}
    $${AndIf} $$0 <> 0
      StrCpy $$LANGUAGE $$0
    $${Else}
      Call Language
    $${EndIf}
  FunctionEnd

  ;Language selection dialog
  Function Language
    Push ""
    """ + languagePushString + r"""
    Push A ; A means auto count languages
    LangDLL::LangDialog "Language Selection" "Please select the language of Syncplay and the installer"
    Pop $$LANGUAGE
    StrCmp $$LANGUAGE "cancel" 0 +2
      Abort
  FunctionEnd

  Function DirectoryCustom

    nsDialogs::Create 1018
    Pop $$Dialog

    GetFunctionAddress $$R8 DirectoryCustomLeave
    nsDialogs::OnBack $$R8

    $${NSD_CreateIcon} 0u 0u 22u 20u ""
    Pop $$Icon_Syncplay
    $${NSD_SetIconFromInstaller} $$Icon_Syncplay $$Icon_Syncplay_Handle

    $${NSD_CreateLabel} 25u 0u 241u 34u "$$(^DirText)"
    Pop $$Label_Text

    $${NSD_CreateText} 8u 38u 187u 12u "$$INSTDIR"
    Pop $$Text_Directory
    $${NSD_SetFocus} $$Text_Directory

    $${NSD_CreateBrowseButton} 202u 37u 55u 14u "$$(^BrowseBtn)"
    Pop $$Button_Browse
    $${NSD_OnClick} $$Button_Browse DirectoryBrowseDialog

    $${NSD_CreateGroupBox} 1u 27u 264u 30u "$$(^DirSubText)"
    Pop $$GroupBox_DirSub

    $${NSD_CreateLabel} 0u 122u 132 8u "$$(^SpaceRequired)$$SizeMB"
    Pop $$Label_Size

    $${NSD_CreateLabel} 321u 122u 132 8u "$$(^SpaceAvailable)$$AvailibleSpaceGiB.$$AvailibleSpaceGB"
    Pop $$Label_Space

    ;$${NSD_CreateCheckBox} 8u 59u 187u 10u "$$(^Associate)"
    ;Pop $$CheckBox_Associate

    $${NSD_CreateCheckBox} 8u 72u 250u 10u "$$(^AutomaticUpdates)"
    Pop $$CheckBox_AutomaticUpdates
    $${NSD_Check} $$CheckBox_AutomaticUpdates

    $${NSD_CreateLabel} 8u 95u 187u 10u "$$(^Shortcut)"
    Pop $$Label_Shortcut

    $${NSD_CreateCheckbox} 8u 105u 70u 10u "$$(^StartMenu)"
    Pop $$CheckBox_StartMenuShortcut

    $${NSD_CreateCheckbox} 78u 105u 70u 10u "$$(^Desktop)"
    Pop $$CheckBox_DesktopShortcut

    $${NSD_CreateCheckbox} 158u 105u 130u 10u "$$(^QuickLaunchBar)"
    Pop $$CheckBox_QuickLaunchShortcut

    ;$${If} $$CheckBox_Associate_State == $${BST_CHECKED}
    ;  $${NSD_Check} $$CheckBox_Associate
    ;$${EndIf}


    $${If} $$CheckBox_StartMenuShortcut_State == $${BST_CHECKED}
      $${NSD_Check} $$CheckBox_StartMenuShortcut
    $${EndIf}

    $${If} $$CheckBox_DesktopShortcut_State == $${BST_CHECKED}
      $${NSD_Check} $$CheckBox_DesktopShortcut
    $${EndIf}

    $${If} $$CheckBox_QuickLaunchShortcut_State == $${BST_CHECKED}
      $${NSD_Check} $$CheckBox_QuickLaunchShortcut
    $${EndIf}

    $${If} $$CheckBox_AutomaticUpdates_State == $${BST_CHECKED}
      $${NSD_Check} $$CheckBox_AutomaticUpdates
    $${EndIf}

    nsDialogs::Show

    $${NSD_FreeIcon} $$Icon_Syncplay_Handle

  FunctionEnd

  Function DirectoryCustomLeave
    $${NSD_GetText} $$Text_Directory $$INSTDIR
    ;$${NSD_GetState} $$CheckBox_Associate $$CheckBox_Associate_State
    $${NSD_GetState} $$CheckBox_AutomaticUpdates $$CheckBox_AutomaticUpdates_State
    $${NSD_GetState} $$CheckBox_StartMenuShortcut $$CheckBox_StartMenuShortcut_State
    $${NSD_GetState} $$CheckBox_DesktopShortcut $$CheckBox_DesktopShortcut_State
    $${NSD_GetState} $$CheckBox_QuickLaunchShortcut $$CheckBox_QuickLaunchShortcut_State
  FunctionEnd

  Function DirectoryBrowseDialog
    nsDialogs::SelectFolderDialog $$(^DirBrowseText)
    Pop $$Directory
    $${If} $$Directory != error
    StrCpy $$INSTDIR $$Directory
    $${NSD_SetText} $$Text_Directory $$INSTDIR
    Call DriveSpace
    $${NSD_SetText} $$Label_Space "$$(^SpaceAvailable)$$AvailibleSpaceGiB.$$AvailibleSpaceGB"
    $${EndIf}
    Abort
  FunctionEnd

  Function GetSize
    StrCpy $$Size "$totalSize"
    IntOp $$Size $$Size / 1024
    IntFmt $$SizeHex "0x%08X" $$Size
    IntOp $$Size $$Size / 1024
  FunctionEnd

  ;Calculates Free Space on HDD
  Function DriveSpace
    StrCpy $$Drive $$INSTDIR 1
    $${DriveSpace} "$$Drive:\" "/D=F /S=M" $$AvailibleSpace
    IntOp $$AvailibleSpaceGiB $$AvailibleSpace / 1024
    IntOp $$AvailibleSpace $$AvailibleSpace % 1024
    IntOp $$AvailibleSpace $$AvailibleSpace / 102
  FunctionEnd

  Function InstallOptions
    ;$${If} $$CheckBox_Associate_State == $${BST_CHECKED}
    ;  Call Associate
    ;  DetailPrint "Associated Syncplay with multimedia files"
    ;$${EndIf}

    $${If} $$CheckBox_StartMenuShortcut_State == $${BST_CHECKED}
      CreateDirectory $$SMPROGRAMS\Syncplay
      SetOutPath "$$INSTDIR"
      CreateShortCut "$$SMPROGRAMS\Syncplay\Syncplay.lnk" "$$INSTDIR\Syncplay.exe" ""
      CreateShortCut "$$SMPROGRAMS\Syncplay\Syncplay Server.lnk" "$$INSTDIR\syncplayServer.exe" ""
      CreateShortCut "$$SMPROGRAMS\Syncplay\Uninstall.lnk" "$$INSTDIR\Uninstall.exe" ""
      WriteINIStr "$$SMPROGRAMS\Syncplay\SyncplayWebsite.url" "InternetShortcut" "URL" "https://syncplay.pl"
    $${EndIf}

    $${If} $$CheckBox_DesktopShortcut_State == $${BST_CHECKED}
      SetOutPath "$$INSTDIR"
      CreateShortCut "$$DESKTOP\Syncplay.lnk" "$$INSTDIR\Syncplay.exe" ""
    $${EndIf}

    $${If} $$CheckBox_QuickLaunchShortcut_State == $${BST_CHECKED}
      SetOutPath "$$INSTDIR"
      CreateShortCut "$$QUICKLAUNCH\Syncplay.lnk" "$$INSTDIR\Syncplay.exe" ""
    $${EndIf}
  FunctionEnd

  ;Associates extensions with Syncplay
  ;Function Associate
  ;  !insertmacro ASSOCIATE avi
  ;  !insertmacro ASSOCIATE mpg
  ;  !insertmacro ASSOCIATE mpeg
  ;  !insertmacro ASSOCIATE mpe
  ;  !insertmacro ASSOCIATE m1v
  ;  !insertmacro ASSOCIATE m2v
  ;  !insertmacro ASSOCIATE mpv2
  ;  !insertmacro ASSOCIATE mp2v
  ;  !insertmacro ASSOCIATE mkv
  ;  !insertmacro ASSOCIATE mp4
  ;  !insertmacro ASSOCIATE m4v
  ;  !insertmacro ASSOCIATE mp4v
  ;  !insertmacro ASSOCIATE 3gp
  ;  !insertmacro ASSOCIATE 3gpp
  ;  !insertmacro ASSOCIATE 3g2
  ;  !insertmacro ASSOCIATE 3pg2
  ;  !insertmacro ASSOCIATE flv
  ;  !insertmacro ASSOCIATE f4v
  ;  !insertmacro ASSOCIATE rm
  ;  !insertmacro ASSOCIATE wmv
  ;  !insertmacro ASSOCIATE swf
  ;  !insertmacro ASSOCIATE rmvb
  ;  !insertmacro ASSOCIATE divx
  ;  !insertmacro ASSOCIATE amv
  ;FunctionEnd

  Function WriteRegistry
    Call GetSize
    WriteRegStr HKLM SOFTWARE\Syncplay "Install_Dir" "$$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "DisplayName" "Syncplay"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "InstallLocation" "$$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "UninstallString" '"$$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "DisplayIcon" "$$INSTDIR\resources\icon.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "Publisher" "Syncplay"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "DisplayVersion" "$version"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "URLInfoAbout" "https://syncplay.pl/"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "EstimatedSize" "$$SizeHex"
    WriteINIStr $$APPDATA\syncplay.ini general language $$(^SyncplayLanguage)
    $${If} $$CheckBox_AutomaticUpdates_State == $${BST_CHECKED}
        WriteINIStr $$APPDATA\syncplay.ini general CheckForUpdatesAutomatically "True"
    $${Else}
        WriteINIStr $$APPDATA\syncplay.ini general CheckForUpdatesAutomatically "False"
    $${EndIf}
  FunctionEnd

  Function un.installConfirm
    nsDialogs::Create 1018
    Pop $$Uninst_Dialog

    $${NSD_CreateIcon} 0u 1u 22u 20u ""
    Pop $$Uninst_Icon
    $${NSD_SetIconFromInstaller} $$Uninst_Icon $$Uninst_Icon_Handle

    $${NSD_CreateLabel} 0u 45u 55u 8u "$$(^UninstallingSubText)"
    Pop $$Uninst_Label_Directory

    $${NSD_CreateLabel} 25u 0u 241u 34u "$$(^UninstallingText)"
    Pop $$Uninst_Label_Text

    ReadRegStr $$INSTDIR HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "InstallLocation"
    $${NSD_CreateText} 56u 43u 209u 12u "$$INSTDIR"
    Pop $$Uninst_Text_Directory
    EnableWindow $$Uninst_Text_Directory 0

    $${NSD_CreateCheckBox} 0u 60u 250u 10u "$$(^UninstConfig)"
    Pop $$Uninst_CheckBox_Config


    nsDialogs::Show
    $${NSD_FreeIcon} $$Uninst_Icon_Handle
  FunctionEnd

  Function un.installConfirmLeave
    $${NSD_GetState} $$Uninst_CheckBox_Config $$Uninst_CheckBox_Config_State
  FunctionEnd

  Function un.AssociateDel
    !insertmacro UNASSOCIATE avi
    !insertmacro UNASSOCIATE mpg
    !insertmacro UNASSOCIATE mpeg
    !insertmacro UNASSOCIATE mpe
    !insertmacro UNASSOCIATE m1v
    !insertmacro UNASSOCIATE m2v
    !insertmacro UNASSOCIATE mpv2
    !insertmacro UNASSOCIATE mp2v
    !insertmacro UNASSOCIATE mkv
    !insertmacro UNASSOCIATE mp4
    !insertmacro UNASSOCIATE m4v
    !insertmacro UNASSOCIATE mp4v
    !insertmacro UNASSOCIATE 3gp
    !insertmacro UNASSOCIATE 3gpp
    !insertmacro UNASSOCIATE 3g2
    !insertmacro UNASSOCIATE 3pg2
    !insertmacro UNASSOCIATE flv
    !insertmacro UNASSOCIATE f4v
    !insertmacro UNASSOCIATE rm
    !insertmacro UNASSOCIATE wmv
    !insertmacro UNASSOCIATE swf
    !insertmacro UNASSOCIATE rmvb
    !insertmacro UNASSOCIATE divx
    !insertmacro UNASSOCIATE amv
  FunctionEnd

  Function un.InstallOptions
    Delete $$SMPROGRAMS\Syncplay\Syncplay.lnk
    Delete "$$SMPROGRAMS\Syncplay\Syncplay Server.lnk"
    Delete $$SMPROGRAMS\Syncplay\Uninstall.lnk
    Delete $$SMPROGRAMS\Syncplay\SyncplayWebsite.url
    RMDir $$SMPROGRAMS\Syncplay
    Delete $$DESKTOP\Syncplay.lnk
    Delete $$QUICKLAUNCH\Syncplay.lnk
    ReadRegStr $$VLC_Directory HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay" "VLCInstallLocation"
    IfFileExists "$$VLC_Directory\lua\intf\syncplay.lua" 0 +2
    Delete $$VLC_Directory\lua\intf\syncplay.lua
  FunctionEnd

  Section "Install"
    SetOverwrite on
    SetOutPath $$INSTDIR
    WriteUninstaller uninstall.exe

    $installFiles

    Call InstallOptions
    Call WriteRegistry
  SectionEnd

  Section "Uninstall"
    Call un.AssociateDel
    Call un.InstallOptions
    $uninstallFiles
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Syncplay"
    DeleteRegKey HKLM SOFTWARE\Syncplay
    Delete $$INSTDIR\uninstall.exe
    RMDir $$INSTDIR\Syncplay\\resources\lua\intf
    RMDir $$INSTDIR\Syncplay\\resources\lua
    RMDir $$INSTDIR\Syncplay\\resources
    RMDir $$INSTDIR\resources
    RMDir $$INSTDIR\lib
    RMDir $$INSTDIR

    $${If} $$Uninst_CheckBox_Config_State == $${BST_CHECKED}
      IfFileExists "$$APPDATA\.syncplay" 0 +2
      Delete $$APPDATA\.syncplay
      IfFileExists "$$APPDATA\syncplay.ini" 0 +2
      Delete $$APPDATA\syncplay.ini
    $${EndIf}
  SectionEnd
"""

class NSISScript(object):
    def create(self):
        fileList, totalSize = self.getBuildDirContents(OUT_DIR)
        print("Total size eq: {}".format(totalSize))
        installFiles = self.prepareInstallListTemplate(fileList)
        uninstallFiles = self.prepareDeleteListTemplate(fileList)

        if os.path.isfile(SETUP_SCRIPT_PATH):
            raise RuntimeError("Cannot create setup script, file exists at {}".format(SETUP_SCRIPT_PATH))
        contents = Template(NSIS_SCRIPT_TEMPLATE).substitute(
            version=syncplay.version,
            uninstallFiles=uninstallFiles,
            installFiles=installFiles,
            totalSize=totalSize,
        )
        with codecs.open(SETUP_SCRIPT_PATH, "w", "utf-8-sig") as outfile:
            outfile.write(contents)

    def compile(self):
        if not os.path.isfile(NSIS_COMPILE):
            return "makensis.exe not found, won't create the installer"
        subproc = subprocess.Popen([NSIS_COMPILE, SETUP_SCRIPT_PATH], env=os.environ)
        subproc.communicate()
        retcode = subproc.returncode
        os.remove(SETUP_SCRIPT_PATH)
        if retcode:
            raise RuntimeError("NSIS compilation return code: %d" % retcode)

    def getBuildDirContents(self, path):
        fileList = {}
        totalSize = 0
        for root, _, files in os.walk(path):
            totalSize += sum(os.path.getsize(os.path.join(root, file_)) for file_ in files)
            for file_ in files:
                new_root = root.replace(OUT_DIR, "").strip("\\")
                if new_root not in fileList:
                    fileList[new_root] = []
                fileList[new_root].append(file_)
        return fileList, totalSize

    def prepareInstallListTemplate(self, fileList):
        create = []
        for dir_ in fileList.keys():
            create.append('SetOutPath "$INSTDIR\\{}"'.format(dir_))
            for file_ in fileList[dir_]:
                create.append('FILE "{}\\{}\\{}"'.format(OUT_DIR, dir_, file_))
        return "\n".join(create)

    def prepareDeleteListTemplate(self, fileList):
        delete = []
        for dir_ in fileList.keys():
            for file_ in fileList[dir_]:
                delete.append('DELETE "$INSTDIR\\{}\\{}"'.format(dir_, file_))
            delete.append('RMdir "$INSTDIR\\{}"'.format(file_))
        return "\n".join(delete)

def pruneUnneededLibraries():
    from pathlib import Path
    cwd = os.getcwd()
    libDir = cwd + '\\' + OUT_DIR + '\\lib\\'
    unneededModules = ['PySide6.Qt3D*', 'PySide6.QtAxContainer.pyd', 'PySide6.QtCharts.pyd', 'PySide6.QtConcurrent.pyd',
                       'PySide6.QtDataVisualization.pyd', 'PySide6.QtHelp.pyd', 'PySide6.QtLocation.pyd',
                       'PySide6.QtMultimedia.pyd', 'PySide6.QtMultimediaWidgets.pyd', 'PySide6.QtOpenGL.pyd',
                       'PySide6.QtPositioning.pyd', 'PySide6.QtPrintSupport.pyd', 'PySide6.QtQml.pyd',
                       'PySide6.QtQuick.pyd', 'PySide6.QtQuickWidgets.pyd', 'PySide6.QtScxml.pyd', 'PySide6.QtSensors.pyd',
                       'PySide6.QtSql.pyd', 'PySide6.QtSvg.pyd', 'PySide6.QtTest.pyd', 'PySide6.QtTextToSpeech.pyd',
                       'PySide6.QtUiTools.pyd', 'PySide6.QtWebChannel.pyd', 'PySide6.QtWebEngine.pyd',
                       'PySide6.QtWebEngineCore.pyd', 'PySide6.QtWebEngineWidgets.pyd', 'PySide6.QtWebSockets.pyd',
                       'PySide6.QtXml.pyd', 'PySide6.QtXmlPatterns.pyd']
    unneededLibs = ['Qt63D*', 'Qt6Charts.dll', 'Qt6Concurrent.dll', 'Qt6DataVisualization.dll', 'Qt6Gamepad.dll', 'Qt6Help.dll',
                    'Qt6Location.dll', 'Qt6Multimedia.dll', 'Qt6MultimediaWidgets.dll', 'Qt6OpenGL.dll', 'Qt6Positioning.dll',
                    'Qt6PrintSupport.dll', 'Qt6Quick.dll', 'Qt6QuickWidgets.dll', 'Qt6Scxml.dll', 'Qt6Sensors.dll', 'Qt6Sql.dll',
                    'Qt6Svg.dll', 'Qt6Test.dll', 'Qt6TextToSpeech.dll', 'Qt6WebChannel.dll', 'Qt6WebEngine.dll',
                    'Qt6WebEngineCore.dll', 'Qt6WebEngineWidgets.dll', 'Qt6WebSockets.dll', 'Qt6Xml.dll',
                    'Qt6XmlPatterns.dll']
    windowsDLL = ['MSVCP140.dll', 'VCRUNTIME140.dll']
    deleteList = unneededModules + unneededLibs + windowsDLL
    deleteList.append('api-*')
    for filename in deleteList:
        for p in Path(libDir).glob(filename):
            p.unlink()

def copyQtPlugins(paths):
    import shutil
    from PySide6 import QtCore
    basePath = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PluginsPath)
    basePath = basePath.replace('/', '\\')
    destBase = os.getcwd() + '\\' + OUT_DIR
    for elem in paths:
        elemDir, elemName = os.path.split(elem)
        source = basePath + '\\' + elem
        dest = destBase + '\\' + elem
        destDir = destBase + '\\' + elemDir
        os.makedirs(destDir, exist_ok=True)
        shutil.copy(source, dest)

class build_installer(py2exe):
    def run(self):
        py2exe.run(self)
        print('*** deleting unnecessary libraries and modules ***')
        pruneUnneededLibraries()
        print('*** copying qt plugins ***')
        copyQtPlugins(qt_plugins)
        script = NSISScript()
        script.create()
        print("*** compiling the NSIS setup script ***")
        script.compile()
        print("*** DONE ***")

guiIcons = glob('syncplay/resources/*.ico') + glob('syncplay/resources/*.png') +  ['syncplay/resources/spinner.mng']

resources = [
    "syncplay/resources/syncplayintf.lua",
    "syncplay/resources/license.rtf",
    "syncplay/resources/third-party-notices.txt"
]
resources.extend(guiIcons)
intf_resources = ["syncplay/resources/lua/intf/syncplay.lua"]

qt_plugins = ['platforms\\qwindows.dll', 'styles\\qmodernwindowsstyle.dll']

common_info = dict(
    name='Syncplay',
    version=syncplay.version,
    author='Uriziel',
    author_email='dev@syncplay.pl',
    description='Syncplay',
)

info = dict(
    common_info,
    packages=['syncplay'],  # Explicitly specify packages to avoid venv discovery
    windows=[{
        "script": "syncplayClient.py",
        "icon_resources": [(1, "syncplay\\resources\\icon.ico")],
        'dest_base': "Syncplay"},
    ],
    console=['syncplayServer.py', {"script":"syncplayClient.py", "icon_resources":[(1, "syncplay\\resources\\icon.ico")], 'dest_base': "SyncplayConsole"}],

    options={
        'py2exe': {
            'dist_dir': OUT_DIR,
            'packages': 'PySide6, cffi, OpenSSL, certifi',
            'includes': 'twisted, sys, encodings, datetime, os, time, math, urllib, ast, unicodedata, _ssl, win32pipe, win32file, sqlite3',
            'excludes': 'venv, venv_py2exe, doctest, pdb, unittest, win32clipboard, win32pdh, win32security, win32trace, win32ui, winxpgui, win32process, tcl, tkinter',
            'dll_excludes': 'msvcr71.dll, MSVCP90.dll, POWRPROF.dll',
            'optimize': 2,
            'compressed': 1
        }
    },
    data_files=[("resources", resources), ("resources/lua/intf", intf_resources)],
    zipfile="lib/libsync.zip",
    cmdclass={"py2exe": build_installer},
)

sys.argv.extend(['py2exe'])
setup(**info)
