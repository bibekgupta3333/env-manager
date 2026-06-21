# PyInstaller spec for env-manager
# Build: pyinstaller env-manager.spec

a = Analysis(
    ['env_manager/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('env_manager/storage/schema.sql', 'env_manager/storage'),
        ('env_manager/dashboard/index.html', 'env_manager/dashboard'),
    ],
    hiddenimports=[
        'env_manager.models',
        'env_manager.storage',
        'env_manager.adapters',
        'env_manager.adapters.python',
        'env_manager.adapters.node',
        'env_manager.adapters.ruby',
        'env_manager.adapters.go',
        'env_manager.adapters.rust',
        'env_manager.discovery',
        'env_manager.cli',
        'env_manager.cli.commands',
        'env_manager.daemon',
        'env_manager.daemon.api',
        'apscheduler',
        'uvicorn',
        'fastapi',
        'rich',
        'typer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='envs',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='envs-dist',
)
