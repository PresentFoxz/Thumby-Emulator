#include <stdint.h>
#include <stddef.h>

#include "py/dynruntime.h"

#include "library.h"
#include "classes.h"

/*
 * This file is intentionally the ONLY MicroPython-facing source file.
 *
 * library.c and classes.c are pure C and can also be reused by a normal
 * firmware build, emulator, test program, etc.
 */

Camera g_camera;


/* ------------------------------------------------------------------------- */
/* library.c wrappers                                                         */
/* ------------------------------------------------------------------------- */

static mp_obj_t py_to_fixed(mp_obj_t a_obj) {
    return mp_obj_new_int(to_fixed(mp_obj_get_float(a_obj)));
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_to_fixed_obj, py_to_fixed);


static mp_obj_t py_from_fixed(mp_obj_t a_obj) {
    return mp_obj_new_float(from_fixed(mp_obj_get_int(a_obj)));
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_from_fixed_obj, py_from_fixed);


static mp_obj_t py_fixed_mul(mp_obj_t a_obj, mp_obj_t b_obj) {
    return mp_obj_new_int(
        fixed_mul(
            mp_obj_get_int(a_obj),
            mp_obj_get_int(b_obj)
        )
    );
}
static MP_DEFINE_CONST_FUN_OBJ_2(py_fixed_mul_obj, py_fixed_mul);


static mp_obj_t py_fixed_div(mp_obj_t a_obj, mp_obj_t b_obj) {
    return mp_obj_new_int(
        fixed_div(
            mp_obj_get_int(a_obj),
            mp_obj_get_int(b_obj)
        )
    );
}
static MP_DEFINE_CONST_FUN_OBJ_2(py_fixed_div_obj, py_fixed_div);


static mp_obj_t py_div_opp(mp_obj_t value_obj) {
    return mp_obj_new_int(
        div_opp(mp_obj_get_int(value_obj))
    );
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_div_opp_obj, py_div_opp);


static mp_obj_t py_mul_opp(mp_obj_t value_obj, mp_obj_t divisor_obj) {
    return mp_obj_new_int(
        mul_opp(
            mp_obj_get_int(value_obj),
            mp_obj_get_int(divisor_obj)
        )
    );
}
static MP_DEFINE_CONST_FUN_OBJ_2(py_mul_opp_obj, py_mul_opp);


static mp_obj_t py_angle_to_index(mp_obj_t angle_obj) {
    return mp_obj_new_int(
        angle_to_index(mp_obj_get_int(angle_obj))
    );
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_angle_to_index_obj, py_angle_to_index);


static mp_obj_t py_fixed_sin(mp_obj_t a_obj) {
    return mp_obj_new_int(
        fixed_sin(mp_obj_get_int(a_obj))
    );
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_fixed_sin_obj, py_fixed_sin);


static mp_obj_t py_fixed_cos(mp_obj_t a_obj) {
    return mp_obj_new_int(
        fixed_cos(mp_obj_get_int(a_obj))
    );
}
static MP_DEFINE_CONST_FUN_OBJ_1(py_fixed_cos_obj, py_fixed_cos);


/* ------------------------------------------------------------------------- */
/* Camera wrappers                                                            */
/* ------------------------------------------------------------------------- */

static mp_obj_t py_camera_init(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 11, 11, false);

    camera_init(
        &g_camera,
        mp_obj_get_float(args[0]),
        mp_obj_get_float(args[1]),
        mp_obj_get_float(args[2]),

        mp_obj_get_float(args[3]),
        mp_obj_get_float(args[4]),
        mp_obj_get_float(args[5]),

        mp_obj_get_float(args[6]),
        mp_obj_get_float(args[7]),

        mp_obj_get_float(args[8]),
        mp_obj_get_float(args[9]),
        mp_obj_get_float(args[10])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_camera_init_obj,
    11,
    11,
    py_camera_init
);


static mp_obj_t py_camera_update(void) {
    camera_update_functions(&g_camera);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    py_camera_update_obj,
    py_camera_update
);


static mp_obj_t py_camera_move(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 6, 6, false);

    CameraButtons btn = {
        .A = mp_obj_is_true(args[0]),
        .B = mp_obj_is_true(args[1]),
        .U = mp_obj_is_true(args[2]),
        .D = mp_obj_is_true(args[3]),
        .L = mp_obj_is_true(args[4]),
        .R = mp_obj_is_true(args[5])
    };

    camera_movement(&g_camera, btn);

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_camera_move_obj,
    6,
    6,
    py_camera_move
);


static mp_obj_t py_camera_get(void) {
    mp_obj_t out[16] = {
        mp_obj_new_int(g_camera.x),
        mp_obj_new_int(g_camera.y),
        mp_obj_new_int(g_camera.z),

        mp_obj_new_int(g_camera.rx),
        mp_obj_new_int(g_camera.ry),
        mp_obj_new_int(g_camera.rz),

        mp_obj_new_int(g_camera.xVel),
        mp_obj_new_int(g_camera.yVel),
        mp_obj_new_int(g_camera.zVel),

        mp_obj_new_int(g_camera.fov),
        mp_obj_new_int(g_camera.near_plane),
        mp_obj_new_int(g_camera.far_plane),

        mp_obj_new_int(g_camera.norm_x),
        mp_obj_new_int(g_camera.norm_y),
        mp_obj_new_int(g_camera.norm_z),

        mp_obj_new_int(g_camera.acc)
    };

    return mp_obj_new_tuple(16, out);
}
static MP_DEFINE_CONST_FUN_OBJ_0(
    py_camera_get_obj,
    py_camera_get
);


/* ------------------------------------------------------------------------- */
/* Transform wrappers                                                         */
/* ------------------------------------------------------------------------- */

static mp_obj_t py_world_to_cam(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 10, 10, false);

    Vec3i r = world_to_cam(
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),

        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),

        mp_obj_get_int(args[6]),
        mp_obj_get_int(args[7]),
        mp_obj_get_int(args[8]),
        mp_obj_get_int(args[9])
    );

    mp_obj_t out[3] = {
        mp_obj_new_int(r.x),
        mp_obj_new_int(r.y),
        mp_obj_new_int(r.z)
    };

    return mp_obj_new_tuple(3, out);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_world_to_cam_obj,
    10,
    10,
    py_world_to_cam
);


static mp_obj_t py_project_point(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 8, 8, false);

    Vec3i r = {
        mp_obj_get_int(args[0]),
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2])
    };

    Vec2i out;

    if (!project_point(
        r,
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),
        mp_obj_get_int(args[6]),
        mp_obj_get_int(args[7]),
        &out
    )) {
        return mp_const_none;
    }

    mp_obj_t result[2] = {
        mp_obj_new_int(out.x),
        mp_obj_new_int(out.y)
    };

    return mp_obj_new_tuple(2, result);
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_project_point_obj,
    8,
    8,
    py_project_point
);


static mp_obj_t py_check_rend(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 8, 8, false);

    return mp_obj_new_int(
        check_rend(
            mp_obj_get_int(args[0]),
            mp_obj_get_int(args[1]),
            mp_obj_get_int(args[2]),
            mp_obj_get_int(args[3]),
            mp_obj_get_int(args[4]),
            mp_obj_get_int(args[5]),
            mp_obj_get_int(args[6]),
            mp_obj_get_int(args[7])
        )
    );
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_check_rend_obj,
    8,
    8,
    py_check_rend
);


/* ------------------------------------------------------------------------- */
/* Buffer wrappers                                                            */
/* ------------------------------------------------------------------------- */

static uint8_t *get_write_buffer(mp_obj_t obj, size_t *len) {
    mp_buffer_info_t info;
    mp_get_buffer_raise(obj, &info, MP_BUFFER_WRITE);

    *len = info.len;
    return (uint8_t *)info.buf;
}


static mp_obj_t py_h_line(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 7, 7, false);

    size_t len;
    uint8_t *buf = get_write_buffer(args[0], &len);

    h_line(
        buf,
        len,
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),
        mp_obj_get_int(args[6])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_h_line_obj,
    7,
    7,
    py_h_line
);


static mp_obj_t py_h_dither_line(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 7, 7, false);

    size_t len;
    uint8_t *buf = get_write_buffer(args[0], &len);

    h_dither_line(
        buf,
        len,
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),
        mp_obj_get_int(args[6])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_h_dither_line_obj,
    7,
    7,
    py_h_dither_line
);


static mp_obj_t py_fill(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 5, 5, false);

    size_t len;
    uint8_t *buf = get_write_buffer(args[0], &len);

    fill_screen(
        buf,
        len,
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_fill_obj,
    5,
    5,
    py_fill
);


static mp_obj_t py_fill_rect(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 9, 9, false);

    size_t len;
    uint8_t *buf = get_write_buffer(args[0], &len);

    fill_rect(
        buf,
        len,
        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),
        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),
        mp_obj_get_int(args[6]),
        mp_obj_get_int(args[7]),
        mp_obj_get_int(args[8])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_fill_rect_obj,
    9,
    9,
    py_fill_rect
);


static mp_obj_t py_custom_tri(size_t n_args, const mp_obj_t *args) {
    mp_arg_check_num(n_args, 0, 12, 12, false);

    size_t len;
    uint8_t *buf = get_write_buffer(args[0], &len);

    custom_tri(
        buf,
        len,

        mp_obj_get_int(args[1]),
        mp_obj_get_int(args[2]),
        mp_obj_get_int(args[3]),

        mp_obj_get_int(args[4]),
        mp_obj_get_int(args[5]),

        mp_obj_get_int(args[6]),
        mp_obj_get_int(args[7]),

        mp_obj_get_int(args[8]),
        mp_obj_get_int(args[9]),

        mp_obj_get_int(args[10]),
        mp_obj_is_true(args[11])
    );

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(
    py_custom_tri_obj,
    12,
    12,
    py_custom_tri
);


/* ------------------------------------------------------------------------- */
/* Module                                                                     */
/* ------------------------------------------------------------------------- */

mp_obj_t mpy_init(
    mp_obj_fun_bc_t *self,
    size_t n_args,
    size_t n_kw,
    mp_obj_t *args
) {
    MP_DYNRUNTIME_INIT_ENTRY

    mp_store_global(
        MP_QSTR___name__,
        MP_OBJ_NEW_QSTR(MP_QSTR_thunder3d)
    );

    mp_store_global(
        MP_QSTR_TO_FIXED_BITS,
        MP_OBJ_FROM_PTR(&py_to_fixed_obj)
    );

    mp_store_global(
        MP_QSTR_FROM_FIXED_BITS,
        MP_OBJ_FROM_PTR(&py_from_fixed_obj)
    );

    mp_store_global(
        MP_QSTR_FIXED_MUL,
        MP_OBJ_FROM_PTR(&py_fixed_mul_obj)
    );

    mp_store_global(
        MP_QSTR_FIXED_DIV,
        MP_OBJ_FROM_PTR(&py_fixed_div_obj)
    );

    mp_store_global(
        MP_QSTR_DIV_OPP,
        MP_OBJ_FROM_PTR(&py_div_opp_obj)
    );

    mp_store_global(
        MP_QSTR_MUL_OPP,
        MP_OBJ_FROM_PTR(&py_mul_opp_obj)
    );

    mp_store_global(
        MP_QSTR_angle_to_index,
        MP_OBJ_FROM_PTR(&py_angle_to_index_obj)
    );

    mp_store_global(
        MP_QSTR_FIXED_SIN,
        MP_OBJ_FROM_PTR(&py_fixed_sin_obj)
    );

    mp_store_global(
        MP_QSTR_FIXED_COS,
        MP_OBJ_FROM_PTR(&py_fixed_cos_obj)
    );

    mp_store_global(
        MP_QSTR_cameraInit,
        MP_OBJ_FROM_PTR(&py_camera_init_obj)
    );

    mp_store_global(
        MP_QSTR_cameraUpdate,
        MP_OBJ_FROM_PTR(&py_camera_update_obj)
    );

    mp_store_global(
        MP_QSTR_cameraMove,
        MP_OBJ_FROM_PTR(&py_camera_move_obj)
    );

    mp_store_global(
        MP_QSTR_cameraGet,
        MP_OBJ_FROM_PTR(&py_camera_get_obj)
    );

    mp_store_global(
        MP_QSTR_worldToCam,
        MP_OBJ_FROM_PTR(&py_world_to_cam_obj)
    );

    mp_store_global(
        MP_QSTR_projectPoint,
        MP_OBJ_FROM_PTR(&py_project_point_obj)
    );

    mp_store_global(
        MP_QSTR_checkRend,
        MP_OBJ_FROM_PTR(&py_check_rend_obj)
    );

    mp_store_global(
        MP_QSTR_h_line,
        MP_OBJ_FROM_PTR(&py_h_line_obj)
    );

    mp_store_global(
        MP_QSTR_h_dither_line,
        MP_OBJ_FROM_PTR(&py_h_dither_line_obj)
    );

    mp_store_global(
        MP_QSTR_fill,
        MP_OBJ_FROM_PTR(&py_fill_obj)
    );

    mp_store_global(
        MP_QSTR_fillRect,
        MP_OBJ_FROM_PTR(&py_fill_rect_obj)
    );

    mp_store_global(
        MP_QSTR_customTri,
        MP_OBJ_FROM_PTR(&py_custom_tri_obj)
    );

    MP_DYNRUNTIME_INIT_EXIT
}
