// SPDX-License-Identifier: MIT
// Public FreeType measurements only; output hashes/metrics, never paths/pixels.
#define _POSIX_C_SOURCE 200809L
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_OUTLINE_H
#include FT_BBOX_H
#include <openssl/evp.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static void check(int condition, const char *message) {
    if (!condition) { fprintf(stderr, "%s\n", message); exit(2); }
}
static EVP_MD_CTX *begin(void) {
    EVP_MD_CTX *c = EVP_MD_CTX_new();
    check(c && EVP_DigestInit_ex(c, EVP_sha256(), NULL), "hash initialization");
    return c;
}
static void finish(EVP_MD_CTX *c, char text[65]) {
    unsigned char data[32]; unsigned size = 0;
    check(EVP_DigestFinal_ex(c, data, &size) && size == 32, "hash finalization");
    EVP_MD_CTX_free(c);
    for (unsigned i = 0; i < 32; ++i) snprintf(text + 2*i, 3, "%02x", data[i]);
}
static void font_hash(const char *path, char text[65]) {
    FILE *f = fopen(path, "rb"); struct stat a, b;
    check(f && !fstat(fileno(f), &a) && S_ISREG(a.st_mode)
          && a.st_size > 0 && a.st_size <= 32*1024*1024, "font size/type");
    EVP_MD_CTX *c = begin(); unsigned char buffer[65536]; long total = 0;
    while (total < a.st_size) {
        size_t size = (size_t)(a.st_size - total);
        if (size > sizeof(buffer)) size = sizeof(buffer);
        size_t got = fread(buffer, 1, size, f);
        check(got && EVP_DigestUpdate(c, buffer, got), "font read/hash"); total += (long)got;
    }
    check(!fstat(fileno(f), &b) && a.st_size == b.st_size
          && a.st_mtim.tv_sec == b.st_mtim.tv_sec && a.st_mtim.tv_nsec == b.st_mtim.tv_nsec,
          "font changed while hashing");
    fclose(f); finish(c, text);
}
typedef struct { EVP_MD_CTX *hash; unsigned commands[4]; } Shape;
static int emit(Shape *s, unsigned char op, const FT_Vector *a,
                const FT_Vector *b, const FT_Vector *c) {
    const FT_Vector *vectors[] = {a,b,c};
    if (++s->commands[op] > 65536 || !EVP_DigestUpdate(s->hash, &op, 1)) return 1;
    for (unsigned i = 0; i < 3 && vectors[i]; ++i) {
        FT_Pos values[] = {vectors[i]->x, vectors[i]->y};
        for (unsigned j = 0; j < 2; ++j) {
            if (values[j] < -16777216 || values[j] > 16777216) return 1;
            uint64_t value = (uint64_t)(int64_t)values[j]; unsigned char bytes[8];
            for (unsigned k = 0; k < 8; ++k) bytes[7-k] = (unsigned char)(value >> (8*k));
            if (!EVP_DigestUpdate(s->hash, bytes, 8)) return 1;
        }
    }
    return 0;
}
static int move_to(const FT_Vector *a, void *s) { return emit(s,0,a,NULL,NULL); }
static int line_to(const FT_Vector *a, void *s) { return emit(s,1,a,NULL,NULL); }
static int conic_to(const FT_Vector *a, const FT_Vector *b, void *s) { return emit(s,2,a,b,NULL); }
static int cubic_to(const FT_Vector *a, const FT_Vector *b, const FT_Vector *c, void *s) { return emit(s,3,a,b,c); }

static void raster(FT_Face face, FT_UInt gid, unsigned ppem) {
    check(!FT_Set_Pixel_Sizes(face, ppem, ppem)
          && !FT_Load_Glyph(face, gid, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP)
          && !FT_Render_Glyph(face->glyph, FT_RENDER_MODE_NORMAL), "unhinted raster load");
    FT_Bitmap *b = &face->glyph->bitmap;
    check(b->pixel_mode == FT_PIXEL_MODE_GRAY && b->num_grays == 256
          && b->width <= 2048 && b->rows <= 2048 && b->pitch >= 0
          && (unsigned)b->pitch >= b->width, "unmeasured raster profile");
    EVP_MD_CTX *hash = begin(); uint64_t coverage = 0; unsigned nonzero = 0;
    for (unsigned y = 0; y < b->rows; ++y) {
        const unsigned char *row = b->buffer + (size_t)y * (unsigned)b->pitch;
        check(EVP_DigestUpdate(hash, row, b->width), "raster hash");
        for (unsigned x = 0; x < b->width; ++x) { coverage += row[x]; nonzero += row[x] != 0; }
    }
    char digest[65]; finish(hash, digest);
    printf("{\"ppem\":%u,\"size\":[%u,%u],\"bearing\":[%d,%d],\"advance_26_6\":[%ld,%ld],"
           "\"nonzero\":%u,\"coverage_sum\":%llu,\"pixels_sha256\":\"%s\"}", ppem,b->width,b->rows,
           face->glyph->bitmap_left,face->glyph->bitmap_top,face->glyph->advance.x,face->glyph->advance.y,
           nonzero,(unsigned long long)coverage,digest);
}

int main(int argc, char **argv) {
    check(argc >= 4 && argc <= 131 && strlen(argv[2]) == 64, "usage: probe font sha256 g:decimal|u:hex ... (max 128)");
    char digest[65]; font_hash(argv[1], digest); check(!strcmp(digest,argv[2]), "font identity mismatch");
    FT_Library library; FT_Face face;
    check(!FT_Init_FreeType(&library) && !FT_New_Face(library,argv[1],0,&face), "font open");
    check(FT_IS_SCALABLE(face) && !FT_IS_TRICKY(face) && !FT_HAS_MULTIPLE_MASTERS(face)
          && face->num_faces == 1 && face->face_index == 0 && face->num_glyphs > 0
          && face->num_glyphs <= 65535 && face->units_per_EM >= 16 && face->units_per_EM <= 16384
          && !FT_Select_Charmap(face, FT_ENCODING_UNICODE), "unmeasured face profile");
    int major,minor,patch; FT_Library_Version(library,&major,&minor,&patch);
    printf("{\"font_sha256\":\"%s\",\"units_per_em\":%u,\"face_index\":0,"
           "\"freetype_version\":[%d,%d,%d],\"glyphs\":[",digest,face->units_per_EM,major,minor,patch);
    for (int i = 3; i < argc; ++i) {
        char *end; const char *request = argv[i];
        check(strlen(request) >= 3 && strlen(request) <= 10 && request[1] == ':'
              && (request[0] == 'g' || request[0] == 'u') && request[2] != '-' && request[2] != '+', "glyph request");
        for (const char *p = request + 2; *p; ++p)
            check((*p >= '0' && *p <= '9') || (request[0] == 'u'
                  && ((*p >= 'a' && *p <= 'f') || (*p >= 'A' && *p <= 'F'))), "glyph request digit");
        errno=0; unsigned long value=strtoul(request+2,&end,request[0]=='g'?10:16);
        check(!errno && !*end && value <= (request[0]=='g'?65535:0x10ffff), "glyph request range");
        FT_UInt gid = request[0]=='g'?(FT_UInt)value:FT_Get_Char_Index(face,value);
        check(gid < (FT_UInt)face->num_glyphs, "glyph outside font");
        if (i > 3) printf(",");
        printf("{\"query_kind\":\"%c\",\"query\":%lu,\"gid\":%u",request[0],value,gid);
        if (!gid) { printf(",\"missing\":true}"); continue; }
        check(!FT_Load_Glyph(face,gid,FT_LOAD_NO_SCALE | FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP)
              && face->glyph->format == FT_GLYPH_FORMAT_OUTLINE
              && !FT_Outline_Check(&face->glyph->outline), "unscaled outline load");
        FT_BBox box; check(!FT_Outline_Get_BBox(&face->glyph->outline,&box), "outline bounds");
        Shape s={.hash=begin(),.commands={0,0,0,0}};
        FT_Outline_Funcs callbacks={move_to,line_to,conic_to,cubic_to,0,0};
        check(!FT_Outline_Decompose(&face->glyph->outline,&callbacks,&s), "outline decomposition limit/error");
        char shape[65]; finish(s.hash,shape);
        printf(",\"bbox_units\":[%ld,%ld,%ld,%ld],\"advance_units\":%ld,"
               "\"commands\":[%u,%u,%u,%u],\"outline_sha256\":\"%s\",\"rasters\":[",
               box.xMin,box.yMin,box.xMax,box.yMax,face->glyph->metrics.horiAdvance,
               s.commands[0],s.commands[1],s.commands[2],s.commands[3],shape);
        raster(face,gid,64);printf(",");raster(face,gid,128);printf("]}");
    }
    printf("]}\n");
    check(!FT_Done_Face(face) && !FT_Done_FreeType(library), "font disposal");
    font_hash(argv[1],digest);check(!strcmp(digest,argv[2]), "font changed during measurements");
    check(!fflush(stdout), "output write");return 0;
}
