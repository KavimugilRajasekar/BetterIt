import subprocess
import sys
import os

def build_executable():
    """
    Builds the BetterIt application into a single executable using PyInstaller.
    """
    print("Starting build process for BetterIt executable...")

    # PyInstaller command components
    # --noconfirm: Replace existing output directory without asking
    # --onefile: Bundle everything into a single .exe
    # --windowed: Do not show a console window when running the app
    # --icon: Set the executable icon
    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "BetterIt",
        "--exclude", "PyQt5",
        "--exclude", "PyQt5-Qt5",
        "--exclude", "PyQt5_sip",
        "--paths", "src",
        "--icon", "assets/pencil.png",
    ]

    # Add data files
    # Syntax for --add-data is "source;destination" on Windows
    # We bundle assets, fonts, and the default config files
    datas = [
        ("assets", "assets"),
        ("fonts", "fonts"),
        ("src/aiwriter/tags.json", "src/aiwriter"),
        ("src/aiwriter/config.json", "src/aiwriter"),
    ]

    for source, dest in datas:
        command.extend(["--add-data", f"{source};{dest}"])

    # The entry point script
    command.append("run.py")

    try:
        # Run the command and stream output to the console
        result = subprocess.run(command, check=True, text=True)
        print("\n" + "="*40)
        print("Build completed successfully!")
        print(f"Executable available at: {os.path.join('dist', 'BetterIt.exe')}")
        print("="*40)
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\nError: PyInstaller not found. Please run 'pip install pyinstaller' first.")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
