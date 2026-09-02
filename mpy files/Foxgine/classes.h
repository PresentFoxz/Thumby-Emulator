#ifndef THUNDER3D_CLASSES_H
#define THUNDER3D_CLASSES_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#include "library.h"

#define DEADZONE (1 << 4)

typedef struct {
    int32_t x;
    int32_t y;
    int32_t z;
} Vec3i;

typedef struct {
    int32_t x;
    int32_t y;
} Vec2i;

typedef struct {
    int a, b, c;
    Vec3i normal;
    uint8_t color;
} Triangle_t;

typedef struct {
    Vec3i *verts;
    Triangle_t *tris;

    int vertCount;
    int triCount;
} Model;

typedef struct {
    Vec2i p[3];
    uint8_t color;
} TriRender;

typedef struct {
    int32_t pos[3];
    int32_t rot[3];
    int32_t size[3];
    int32_t idx;
} Entity;

typedef struct {
    Vec3i pos;
    Vec3i rot;
    Vec3i vel;

    int32_t acc;
    int32_t frict;
    int32_t fov;

    Vec2i plane;
    Vec2i rDir;
    Vec3i norm;
    Vec2i sin;
    Vec2i cos;
} Camera;

typedef struct {
    bool A;
    bool B;
    bool U;
    bool D;
    bool L;
    bool R;
} CameraButtons;

void entity_init(
    Entity *ent,
    int32_t x, int32_t y, int32_t z,
    int32_t rx, int32_t ry, int32_t rz,
    int32_t sx, int32_t sy, int32_t sz,
    int32_t idx
);

void camera_init(
    Camera *cam,
    float x, float y, float z,
    float rx, float ry, float rz,
    float near_plane, float far_plane,
    float acc, float frict, float fov
);

void camera_update_functions(Camera *cam);
void camera_movement(Camera *cam, CameraButtons btn);

Vec3i world_to_cam(
    int32_t cx, int32_t cy, int32_t cz,
    int32_t vx, int32_t vy, int32_t vz,
    int32_t sinX, int32_t sinY,
    int32_t cosX, int32_t cosY
);

bool project_point(
    Vec3i r,
    int32_t mX,
    int32_t mY,
    int32_t fov,
    int32_t near_plane,
    int32_t far_plane,
    Vec2i *out
);

int check_rend(
    int32_t x0, int32_t y0,
    int32_t x1, int32_t y1,
    int32_t x2, int32_t y2,
    int32_t width, int32_t height
);

void h_line(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t y,
    int32_t x_start,
    int32_t x_end,
    int32_t color
);

void h_dither_line(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t y,
    int32_t x_start,
    int32_t x_end,
    int32_t color
);

void plot_pixel(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t x,
    int32_t y,
    int32_t color
);

void fill_screen(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t interlace,
    int32_t color
);

void fill_rect(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t interlace,
    int32_t x,
    int32_t y,
    int32_t w,
    int32_t h,
    int32_t color
);

void custom_tri(
    uint8_t *buf,
    size_t buf_len,
    int32_t width,
    int32_t height,
    int32_t interlace,
    int32_t x0, int32_t y0,
    int32_t x1, int32_t y1,
    int32_t x2, int32_t y2,
    int32_t color,
    bool fill
);

int load_obj(const char *filename);

#endif
