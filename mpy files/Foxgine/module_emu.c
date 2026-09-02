#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdint.h>
#include <stddef.h>

#include "library.h"
#include "classes.h"

Camera g_camera;


/* ------------------------------------------------------------------------- */
/* library.c wrappers                                                         */
/* ------------------------------------------------------------------------- */

static PyObject *init_game(PyObject *self, PyObject *args) {
    
}


/* ------------------------------------------------------------------------- */
/* Camera wrappers                                                            */
/* ------------------------------------------------------------------------- */

static PyObject *py_camera_init(PyObject *self, PyObject *args) {
    float x;
    float y;
    float z;

    float rx;
    float ry;
    float rz;

    float near_plane;
    float far_plane;

    float acc;
    float frict;
    float fov;

    if (!PyArg_ParseTuple(args, "fffffffffff", &x, &y, &z, &rx, &ry, &rz, &near_plane, &far_plane, &acc, &frict, &fov)) return NULL;

    camera_init(
        &g_camera,

        (float)x,
        (float)y,
        (float)z,

        (float)rx,
        (float)ry,
        (float)rz,

        (float)near_plane,
        (float)far_plane,

        (float)acc,
        (float)frict,
        (float)fov
    );

    Py_RETURN_NONE;
}


static PyObject *py_camera_update(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    camera_update_functions(&g_camera);

    Py_RETURN_NONE;
}


static PyObject *py_camera_move(PyObject *self, PyObject *args)
{
    int A;
    int B;
    int U;
    int D;
    int L;
    int R;

    if (!PyArg_ParseTuple(
        args,
        "pppppp",
        &A,
        &B,
        &U,
        &D,
        &L,
        &R
    ))
        return NULL;

    CameraButtons btn = {
        .A = A != 0,
        .B = B != 0,
        .U = U != 0,
        .D = D != 0,
        .L = L != 0,
        .R = R != 0
    };

    camera_movement(
        &g_camera,
        btn
    );

    Py_RETURN_NONE;
}


static PyObject *py_camera_get(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    return Py_BuildValue(
        "(iiiiiiiiiiiiiiii)",

        g_camera.x,
        g_camera.y,
        g_camera.z,

        g_camera.rx,
        g_camera.ry,
        g_camera.rz,

        g_camera.xVel,
        g_camera.yVel,
        g_camera.zVel,

        g_camera.fov,

        g_camera.near_plane,
        g_camera.far_plane,

        g_camera.norm_x,
        g_camera.norm_y,
        g_camera.norm_z,

        g_camera.acc
    );
}


/* ------------------------------------------------------------------------- */
/* Transform wrappers                                                         */
/* ------------------------------------------------------------------------- */

static PyObject *py_world_to_cam(PyObject *self, PyObject *args)
{
    int cx;
    int cy;
    int cz;

    int vx;
    int vy;
    int vz;

    int sinX;
    int sinY;

    int cosX;
    int cosY;

    if (!PyArg_ParseTuple(
        args,
        "iiiiiiiiii",

        &cx,
        &cy,
        &cz,

        &vx,
        &vy,
        &vz,

        &sinX,
        &sinY,

        &cosX,
        &cosY
    ))
        return NULL;

    Vec3i r = world_to_cam(
        (int32_t)cx,
        (int32_t)cy,
        (int32_t)cz,

        (int32_t)vx,
        (int32_t)vy,
        (int32_t)vz,

        (int32_t)sinX,
        (int32_t)sinY,

        (int32_t)cosX,
        (int32_t)cosY
    );

    return Py_BuildValue(
        "(iii)",
        r.x,
        r.y,
        r.z
    );
}


static PyObject *py_project_point(PyObject *self, PyObject *args) {
    int x;
    int y;
    int z;

    int mX;
    int mY;

    int fov;
    int near_plane;
    int far_plane;

    if (!PyArg_ParseTuple(
        args,
        "iiiiiiii",

        &x,
        &y,
        &z,

        &mX,
        &mY,

        &fov,
        &near_plane,
        &far_plane
    ))
        return NULL;

    Vec3i r = {
        (int32_t)x,
        (int32_t)y,
        (int32_t)z
    };

    Vec2i out;

    if (!project_point(
        r,

        (int32_t)mX,
        (int32_t)mY,

        (int32_t)fov,
        (int32_t)near_plane,
        (int32_t)far_plane,

        &out
    )) {
        Py_RETURN_NONE;
    }

    return Py_BuildValue(
        "(ii)",
        out.x,
        out.y
    );
}


static PyObject *py_check_rend(PyObject *self, PyObject *args) {
    int x0;
    int y0;

    int x1;
    int y1;

    int x2;
    int y2;

    int width;
    int height;

    if (!PyArg_ParseTuple(
        args,
        "iiiiiiii",

        &x0,
        &y0,

        &x1,
        &y1,

        &x2,
        &y2,

        &width,
        &height
    ))
        return NULL;

    return PyLong_FromLong(
        (long)check_rend(
            (int32_t)x0,
            (int32_t)y0,

            (int32_t)x1,
            (int32_t)y1,

            (int32_t)x2,
            (int32_t)y2,

            (int32_t)width,
            (int32_t)height
        )
    );
}


/* ------------------------------------------------------------------------- */
/* Buffer helpers                                                             */
/* ------------------------------------------------------------------------- */

static int get_write_buffer(PyObject *obj, Py_buffer *view) {
    if (PyObject_GetBuffer(
        obj,
        view,
        PyBUF_WRITABLE | PyBUF_SIMPLE
    ) != 0) {
        return 0;
    }

    return 1;
}


/* ------------------------------------------------------------------------- */
/* Rendering wrappers                                                         */
/* ------------------------------------------------------------------------- */

static PyObject *py_h_line(PyObject *self, PyObject *args)
{
    PyObject *buf_obj;

    int width;
    int height;

    int y;
    int x_start;
    int x_end;

    int color;

    if (!PyArg_ParseTuple(
        args,
        "Oiiiiii",

        &buf_obj,

        &width,
        &height,

        &y,
        &x_start,
        &x_end,

        &color
    ))
        return NULL;

    Py_buffer view;

    if (!get_write_buffer(
        buf_obj,
        &view
    ))
        return NULL;

    h_line(
        (uint8_t *)view.buf,
        (size_t)view.len,

        (int32_t)width,
        (int32_t)height,

        (int32_t)y,
        (int32_t)x_start,
        (int32_t)x_end,

        (int32_t)color
    );

    PyBuffer_Release(&view);

    Py_RETURN_NONE;
}


static PyObject *py_h_dither_line(PyObject *self, PyObject *args)
{
    PyObject *buf_obj;

    int width;
    int height;

    int y;
    int x_start;
    int x_end;

    int color;

    if (!PyArg_ParseTuple(
        args,
        "Oiiiiii",

        &buf_obj,

        &width,
        &height,

        &y,
        &x_start,
        &x_end,

        &color
    ))
        return NULL;

    Py_buffer view;

    if (!get_write_buffer(
        buf_obj,
        &view
    ))
        return NULL;

    h_dither_line(
        (uint8_t *)view.buf,
        (size_t)view.len,

        (int32_t)width,
        (int32_t)height,

        (int32_t)y,
        (int32_t)x_start,
        (int32_t)x_end,

        (int32_t)color
    );

    PyBuffer_Release(&view);

    Py_RETURN_NONE;
}


static PyObject *py_fill(PyObject *self, PyObject *args)
{
    PyObject *buf_obj;

    int width;
    int height;
    int interlace;
    int color;

    if (!PyArg_ParseTuple(
        args,
        "Oiiii",

        &buf_obj,

        &width,
        &height,
        &interlace,
        &color
    ))
        return NULL;

    Py_buffer view;

    if (!get_write_buffer(
        buf_obj,
        &view
    ))
        return NULL;

    fill_screen(
        (uint8_t *)view.buf,
        (size_t)view.len,

        (int32_t)width,
        (int32_t)height,
        (int32_t)interlace,
        (int32_t)color
    );

    PyBuffer_Release(&view);

    Py_RETURN_NONE;
}


static PyObject *py_fill_rect(PyObject *self, PyObject *args) {
    PyObject *buf_obj;

    int width;
    int height;
    int interlace;

    int x;
    int y;
    int w;
    int h;

    int color;

    if (!PyArg_ParseTuple(args, "Oiiiiiiii", &buf_obj, &width, &height, &interlace, &x, &y, &w, &h, &color)) return NULL;

    Py_buffer view;
    if (!get_write_buffer(buf_obj, &view)) return NULL;

    fill_rect(
        (uint8_t *)view.buf,
        (size_t)view.len,

        (int32_t)width,
        (int32_t)height,
        (int32_t)interlace,

        (int32_t)x,
        (int32_t)y,
        (int32_t)w,
        (int32_t)h,

        (int32_t)color
    );

    PyBuffer_Release(&view);

    Py_RETURN_NONE;
}

static PyObject *py_load_objects(PyObject *self, PyObject *args) {
    const char *filename;

    if (!PyArg_ParseTuple(args, "si", &filename, &texture)) { return NULL; }

    int model_id = load_obj(filename);

    if (model_id < 0) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to load OBJ");
        return NULL;
    }

    return PyLong_FromLong(model_id);
}

static PyObject *py_draw_triangle(PyObject *self, PyObject *args) {
    PyObject *buf_obj;

    int x0;
    int y0;

    int x1;
    int y1;

    int x2;
    int y2;

    int color;
    int fill;

    if (!PyArg_ParseTuple(
        args,
        "Oiiiiiiiiiip",

        &buf_obj,

        &width,
        &height,
        &interlace,

        &x0,
        &y0,

        &x1,
        &y1,

        &x2,
        &y2,

        &color,
        &fill
    ))
        return NULL;

    Py_buffer view;

    if (!get_write_buffer(
        buf_obj,
        &view
    ))
        return NULL;

    custom_tri(
        (uint8_t *)view.buf,
        (size_t)view.len,

        (int32_t)width,
        (int32_t)height,
        (int32_t)interlace,

        (int32_t)x0,
        (int32_t)y0,

        (int32_t)x1,
        (int32_t)y1,

        (int32_t)x2,
        (int32_t)y2,

        (int32_t)color,
        fill != 0
    );

    PyBuffer_Release(&view);

    Py_RETURN_NONE;
}


/* ------------------------------------------------------------------------- */
/* Method table                                                               */
/* ------------------------------------------------------------------------- */

static PyMethodDef T3DMethods[] = {

    {
        "cameraUpdate",
        py_camera_update,
        METH_VARARGS,
        NULL
    },

    {
        "cameraMove",
        py_camera_move,
        METH_VARARGS,
        NULL
    },

    {
        "cameraGet",
        py_camera_get,
        METH_VARARGS,
        NULL
    },

    {
        "projectPoint",
        py_project_point,
        METH_VARARGS,
        NULL
    },

    {
        "checkRend",
        py_check_rend,
        METH_VARARGS,
        NULL
    },

    {
        "h_line",
        py_h_line,
        METH_VARARGS,
        NULL
    },

    {
        "h_dither_line",
        py_h_dither_line,
        METH_VARARGS,
        NULL
    },

    {
        "fill",
        py_fill,
        METH_VARARGS,
        NULL
    },

    {
        "fillRect",
        py_fill_rect,
        METH_VARARGS,
        NULL
    },

    {
        "drawTriangle",
        py_draw_triangle,
        METH_VARARGS,
        NULL
    },

    {
        "loadOBJ",
        py_load_objects,
        METH_VARARGS,
        NULL
    },

    {
        NULL,
        NULL,
        0,
        NULL
    }
};


/* ------------------------------------------------------------------------- */
/* Module definition                                                          */
/* ------------------------------------------------------------------------- */

static struct PyModuleDef T3DModule = { PyModuleDef_HEAD_INIT, "T3D_EMU", NULL, -1, T3DMethods };


/* ------------------------------------------------------------------------- */
/* Module init                                                                */
/* ------------------------------------------------------------------------- */

PyMODINIT_FUNC PyInit_T3D_EMU(void) {
    PyObject *module = PyModule_Create(&T3DModule);

    if (module == NULL) return NULL;

    return module;
}