#ifndef THUNDER3D_LIBRARY_H
#define THUNDER3D_LIBRARY_H

#include <stdint.h>

#define FIXED_BITS 8
#define FP24X8_ONE (1 << FIXED_BITS)

#define TABLE_SIZE 256
#define TABLE_SIZE_LUT 520
#define FP16X16_ONE (1 << 16)

#define CHUNK_WIDTH  1
#define CHUNK_HEIGHT 1
#define CHUNK_DEPTH  1
#define CHUNK_AMT    (CHUNK_WIDTH * CHUNK_HEIGHT * CHUNK_DEPTH)

#define CHUNK_X 1
#define CHUNK_Y 1
#define CHUNK_Z 1
#define CHUNK_SIZE (CHUNK_X * CHUNK_Y * CHUNK_Z)

#define MAX_TRIS_CHUNK (CHUNK_SIZE * 12)
#define MAX_TRIS       (MAX_TRIS_CHUNK * CHUNK_AMT)
#define MAX_SPRT       0
#define MAX_DEPTH      20

#define EVEN_MASK 0x55
#define ODD_MASK  0xAA

extern uint8_t *buf;
extern int width;
extern int height;
extern int w_Half;
extern int h_Half;

extern uint8_t BAYER4x4_FLAT[16];

extern int interlace;
extern int frameCount;

extern const int16_t SIN_FIXED[TABLE_SIZE];
extern const int16_t COS_FIXED[TABLE_SIZE];

int32_t to_fixed(float a);
float   from_fixed(int32_t a);

int32_t div_opp(int32_t value);
int32_t mul_opp(int32_t value, int32_t divisor);

int32_t fixed_mul(int32_t a, int32_t b);
int32_t fixed_div(int32_t a, int32_t b);

int32_t angle_to_index(int32_t fixed_angle);
int32_t fixed_sin(int32_t a);
int32_t fixed_cos(int32_t a);

#endif
