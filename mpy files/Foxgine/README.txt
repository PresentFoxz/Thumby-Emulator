PURE C THUMBY NATIVE MODULE
===========================

Structure:

    library.c
    library.h
    classes.c
    classes.h
    module.c
    Makefile

library.c / classes.c
---------------------
These are pure C. They do not include MicroPython headers and do not use:
- mp_obj_t
- MP_QSTR
- MP_DEFINE_CONST_FUN_OBJ
- mp_store_global
- dynruntime APIs

They can be reused outside MicroPython.

module.c
--------
This is the only MicroPython-specific file.

It converts Python arguments to normal C values, calls the pure C engine, then
converts the result back to Python.

Build
-----

    make MPY_DIR="/e/path/to/micropython"

The three C files are compiled/linked into:

    thunder3d.mpy

Original-source coverage
------------------------
This package ports the core library.py fixed-point/trig math and the
performance-critical camera/transform/raster functions from classes.py.

The remaining classes.py functions that depend heavily on nested Python
lists/objects (directVerts, setupSprite, insertion_sort, renderWorld, )
are not yet represented in this first pure-C package. They should be ported
using C structs/arrays rather than wrapping the nested Python representation;
otherwise much of the benefit of moving them to C is lost.
