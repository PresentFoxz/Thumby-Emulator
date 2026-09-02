#include "classes.h"

static const uint8_t BAYER4x4_FLAT[16] = {
    0, 8, 2, 10,
    12, 4, 14, 6,
    3, 11, 1, 9,
    15, 7, 13, 5
};

void entity_init(
    Entity *ent,
    int32_t x, int32_t y, int32_t z,
    int32_t rx, int32_t ry, int32_t rz,
    int32_t sx, int32_t sy, int32_t sz,
    int32_t idx
) {
    ent->pos[0] = x;
    ent->pos[1] = y;
    ent->pos[2] = z;

    ent->rot[0] = rx;
    ent->rot[1] = ry;
    ent->rot[2] = rz;

    ent->size[0] = sx;
    ent->size[1] = sy;
    ent->size[2] = sz;

    ent->idx = idx;
}

void camera_init(
    Camera *cam,
    float x, float y, float z,
    float rx, float ry, float rz,
    float near_plane, float far_plane,
    float acc, float frict, float fov
) {
    cam->pos.x = to_fixed(x);
    cam->pos.y = to_fixed(y);
    cam->pos.z = to_fixed(z);

    cam->rot.x = to_fixed(rx);
    cam->rot.y = to_fixed(ry);
    cam->rot.z = to_fixed(rz);

    cam->vel.x = 0;
    cam->vel.y = 0;
    cam->vel.z = 0;

    cam->acc = to_fixed(acc);
    cam->frict = to_fixed(frict);
    cam->fov = to_fixed(fov);

    cam->plane.x = to_fixed(near_plane);
    cam->plane.y = to_fixed(far_plane);

    cam->rDir.x = to_fixed(1.2f);
    cam->rDir.y = to_fixed(1.2f);

    cam->norm.x = 0;
    cam->norm.y = 0;
    cam->norm.z = to_fixed(1.0f);

    cam->sin.y = 0;
    cam->cos.y = FP24X8_ONE;
    cam->sin.x = 0;
    cam->cos.x = FP24X8_ONE;
}

void camera_update_functions(Camera *cam) {
    int32_t yaw = angle_to_index(cam->rot.y);
    int32_t pitch = angle_to_index(cam->rot.x);

    cam->sin.y = fixed_sin(yaw);
    cam->cos.y = fixed_cos(yaw);
    cam->sin.x = fixed_sin(pitch);
    cam->cos.x = fixed_cos(pitch);

    cam->norm.x = fixed_mul(cam->sin.y, cam->cos.x);
    cam->norm.y = -cam->sin.x;
    cam->norm.z = fixed_mul(cam->cos.y, cam->cos.x);
}

void camera_movement(Camera *cam, CameraButtons btn) {
    int32_t yaw = angle_to_index(cam->rot.y);
    int32_t sin = fixed_sin(yaw);
    int32_t cos = fixed_cos(yaw);

    if (btn.A) {
        if (btn.U) cam->vel.x += cam->acc;
        if (btn.D) cam->vel.y -= cam->acc;
    } else if (btn.B) {
        if (btn.U) cam->rot.x += cam->rDir.x;
        if (btn.D) cam->rot.x -= cam->rDir.x;

        if (btn.L) cam->rot.y -= cam->rDir.y;
        if (btn.R) cam->rot.y += cam->rDir.y;

        int32_t max_pitch = to_fixed(68.0f);

        if (cam->rot.x > max_pitch) cam->rot.x = max_pitch;
        if (cam->rot.x < -max_pitch) cam->rot.x = -max_pitch;
    } else {
        if (btn.U) {
            cam->vel.x += fixed_mul(cam->acc, sin);
            cam->vel.z += fixed_mul(cam->acc, cos);
        }

        if (btn.D) {
            cam->vel.x -= fixed_mul(cam->acc, sin);
            cam->vel.z -= fixed_mul(cam->acc, cos);
        }

        if (btn.L) {
            cam->vel.x -= fixed_mul(cam->acc, cos);
            cam->vel.z += fixed_mul(cam->acc, sin);
        }

        if (btn.R) {
            cam->vel.x += fixed_mul(cam->acc, cos);
            cam->vel.z -= fixed_mul(cam->acc, sin);
        }
    }

    cam->vel.x = fixed_mul(cam->vel.x, cam->frict);
    cam->vel.y = fixed_mul(cam->vel.y, cam->frict);
    cam->vel.z = fixed_mul(cam->vel.z, cam->frict);

    if (cam->vel.x > -DEADZONE && cam->vel.x < DEADZONE) cam->vel.x = 0;
    if (cam->vel.y > -DEADZONE && cam->vel.y < DEADZONE) cam->vel.y = 0;
    if (cam->vel.z > -DEADZONE && cam->vel.z < DEADZONE) cam->vel.z = 0;

    cam->pos.x += cam->vel.x;
    cam->pos.y += cam->vel.y;
    cam->pos.z += cam->vel.z;
}

Vec3i world_to_cam(
    int32_t cx, int32_t cy, int32_t cz,
    int32_t vx, int32_t vy, int32_t vz,
    int32_t sinX, int32_t sinY,
    int32_t cosX, int32_t cosY
) {
    int32_t nx = vx - cx;
    int32_t ny = vy - cy;
    int32_t nz = vz - cz;

    int32_t dz =
        fixed_mul(sinY, nx) +
        fixed_mul(cosY, nz);

    Vec3i out;

    out.x =
        fixed_mul(cosY, nx) -
        fixed_mul(sinY, nz);

    out.y = -(
        fixed_mul(cosX, ny) -
        fixed_mul(sinX, dz)
    );

    out.z =
        fixed_mul(sinX, ny) +
        fixed_mul(cosX, dz);

    return out;
}

bool project_point(
    Vec3i r,
    int32_t mX,
    int32_t mY,
    int32_t fov,
    int32_t near_plane,
    int32_t far_plane,
    Vec2i *out
) {
    if (r.z <= near_plane || r.z >= far_plane) {
        return false;
    }

    int32_t z = r.z;
    if (z == 0) {
        z = 1;
    }

    int32_t x2d = fixed_div(r.x, z);
    int32_t y2d = fixed_div(r.y, z);

    x2d = fixed_mul(x2d, fov) + mX;
    y2d = fixed_mul(y2d, fov) + mY;

    out->x = x2d >> FIXED_BITS;
    out->y = y2d >> FIXED_BITS;

    return true;
}

int check_rend(
    int32_t x0, int32_t y0,
    int32_t x1, int32_t y1,
    int32_t x2, int32_t y2,
    int32_t width, int32_t height
) {
    int32_t minX = x0;
    int32_t maxX = x0;
    int32_t minY = y0;
    int32_t maxY = y0;

    if (x1 < minX) minX = x1;
    if (x2 < minX) minX = x2;
    if (x1 > maxX) maxX = x1;
    if (x2 > maxX) maxX = x2;

    if (y1 < minY) minY = y1;
    if (y2 < minY) minY = y2;
    if (y1 > maxY) maxY = y1;
    if (y2 > maxY) maxY = y2;

    if (
        maxX < 0 ||
        minX >= width ||
        maxY < 0 ||
        minY >= height
    ) {
        return 1;
    }

    return 0;
}

void h_line(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t y, int32_t x_start, int32_t x_end, int32_t color) {
    if (y < 0 || y >= height) return;

    if (x_start < 0) x_start = 0;
    if (x_end > width) x_end = width;
    if (x_start >= x_end) return;

    int32_t page = y >> 3;
    int32_t bit = y & 7;
    uint8_t mask = (uint8_t)(1u << bit);
    uint8_t inv = (uint8_t)(255u - mask);
    int32_t row = page * width;

    for (int32_t x = x_start; x < x_end; ++x) {
        size_t idx = (size_t)(row + x);
        if (idx >= buf_len) break;

        if (color) {
            buf[idx] |= mask;
        } else {
            buf[idx] &= inv;
        }
    }
}

void h_dither_line(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t y, int32_t x_start, int32_t x_end, int32_t color) {
    if (y < 0 || y >= height) return;

    if (x_start < 0) x_start = 0;
    if (x_end > width) x_end = width;
    if (x_start >= x_end) return;

    int32_t page = y >> 3;
    int32_t bit = y & 7;
    uint8_t mask = (uint8_t)(1u << bit);
    uint8_t inv = (uint8_t)(255u - mask);
    int32_t row = page * width;

    int32_t color_scaled = mul_opp(color * 16, 3);
    int32_t yb = (y & 3) << 2;

    for (int32_t x = x_start; x < x_end; ++x) {
        size_t idx = (size_t)(row + x);
        if (idx >= buf_len) break;

        int32_t threshold = BAYER4x4_FLAT[yb + (x & 3)];

        if (color_scaled > threshold) {
            buf[idx] |= mask;
        } else {
            buf[idx] &= inv;
        }
    }
}

void plot_pixel(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t x, int32_t y, int32_t color) {
    if (x < 0 || x >= width || y < 0 || y >= height) {
        return;
    }

    size_t idx = (size_t)((y >> 3) * width + x);
    if (idx >= buf_len) {
        return;
    }

    uint8_t mask = (uint8_t)(1u << (y & 7));

    if (color) {
        buf[idx] |= mask;
    } else {
        buf[idx] &= (uint8_t)~mask;
    }
}

void fill_screen(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t interlace, int32_t color) {
    for (int32_t y = interlace; y < height; y += 2) {
        h_line(buf, buf_len, width, height, y, 0, width, color);
    }
}

void fill_rect(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t interlace, int32_t x, int32_t y, int32_t w, int32_t h, int32_t color) {
    int32_t x_end = x + w;

    for (int32_t yy = y; yy < y + h; ++yy) {
        if ((yy & 1) != interlace) {
            continue;
        }

        h_line(
            buf, buf_len,
            width, height,
            yy, x, x_end,
            color
        );
    }
}

void custom_tri(uint8_t *buf, size_t buf_len, int32_t width, int32_t height, int32_t interlace, int32_t x0, int32_t y0, int32_t x1, int32_t y1, int32_t x2, int32_t y2, int32_t color, bool fill) {
    int32_t t;

    if (y1 < y0) {
        t = x0; x0 = x1; x1 = t;
        t = y0; y0 = y1; y1 = t;
    }

    if (y2 < y0) {
        t = x0; x0 = x2; x2 = t;
        t = y0; y0 = y2; y2 = t;
    }

    if (y2 < y1) {
        t = x1; x1 = x2; x2 = t;
        t = y1; y1 = y2; y2 = t;
    }

    if (y0 == y2) {
        return;
    }

    const int32_t FP = 8;
    const int32_t scale = 1 << FP;

    int32_t dy02 = y2 - y0;
    int32_t dy01 = y1 - y0;
    int32_t dy12 = y2 - y1;

    int32_t dx02 =
        dy02 != 0
        ? mul_opp((x2 - x0) * scale, dy02)
        : 0;

    int32_t dx01 =
        dy01 != 0
        ? mul_opp((x1 - x0) * scale, dy01)
        : 0;

    int32_t dx12 =
        dy12 != 0
        ? mul_opp((x2 - x1) * scale, dy12)
        : 0;

    int32_t xA = x0 * scale;
    int32_t xB = x0 * scale;

    int32_t y = y0;

    while (y < y1) {
        if (
            y >= 0 &&
            y < height &&
            ((y & 1) == interlace)
        ) {
            int32_t xa = xA >> FP;
            int32_t xb = xB >> FP;

            if (xa > xb) {
                t = xa;
                xa = xb;
                xb = t;
            }

            if (fill) {
                h_dither_line(
                    buf, buf_len,
                    width, height,
                    y, xa, xb + 1,
                    color
                );
            } else {
                plot_pixel(buf, buf_len, width, height, xa, y, color);
                plot_pixel(buf, buf_len, width, height, xb, y, color);
            }
        }

        xA += dx02;
        xB += dx01;
        ++y;
    }

    xB = x1 * scale;

    while (y < y2) {
        if (
            y >= 0 &&
            y < height &&
            ((y & 1) == interlace)
        ) {
            int32_t xa = xA >> FP;
            int32_t xb = xB >> FP;

            if (xa > xb) {
                t = xa;
                xa = xb;
                xb = t;
            }

            if (fill) {
                h_dither_line(
                    buf, buf_len,
                    width, height,
                    y, xa, xb + 1,
                    color
                );
            } else {
                plot_pixel(buf, buf_len, width, height, xa, y, color);
                plot_pixel(buf, buf_len, width, height, xb, y, color);
            }
        }

        xA += dx02;
        xB += dx12;
        ++y;
    }
}
