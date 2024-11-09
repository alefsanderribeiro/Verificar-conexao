import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["os", "subprocess", "json", "datetime", "time", "platform"],
    "include_files": [],
    "excludes": []
}

base = None
if sys.platform == "win32":
    base = "Console"  # Use "Win32GUI" para aplicações sem console

setup(
    name="Monitor de Ping",
    version="0.0.1",
    description="Monitoramento de Ping com Histórico",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            icon="Monitor de Ping.ico",
            target_name="Monitor de Ping.exe"
        )
    ]
)
