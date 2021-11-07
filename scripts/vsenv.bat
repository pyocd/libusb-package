rem From: https://renenyffenegger.ch/notes/development/tools/scripts/personal/vsenv_bat

@echo off

rem
rem Uncomment setting VSCMD_DEBUG to enable debugging to output
rem
rem set VSCMD_DEBUG=3

rem
rem   Determine path to VsDevCmd.bat
rem
for /f "usebackq delims=#" %%a in (`"%programfiles(x86)%\Microsoft Visual Studio\Installer\vswhere" -latest -property installationPath`) do set VsDevCmd_Path=%%a\Common7\Tools\VsDevCmd.bat

if [%1] equ [64] (

  "%VsDevCmd_Path%" -arch=amd64

) else (

  "%VsDevCmd_Path%"

)

rem set VSCMD_DEBUG=
set VsDevCmd_Path=
