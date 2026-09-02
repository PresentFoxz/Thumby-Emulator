from setuptools import setup, Extension

setup(
    name="T3D_EMU",
    version="1.0",
    ext_modules=[
        Extension(
            "T3D_EMU",
            sources=[
                "library.c",
                "classes.c",
                "module_emu.c",
            ],
        )
    ],
)