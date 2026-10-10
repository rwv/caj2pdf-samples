// SPDX-License-Identifier: MIT
// Observe documented FreeType mappings/loads, without extracting glyph programs.
#define _GNU_SOURCE
#include <ft2build.h>
#include FT_FREETYPE_H
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stdatomic.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <time.h>
#ifndef FT_OBSERVE_DIRECTORY
#define FT_OBSERVE_DIRECTORY "/output"
#endif
static _Atomic unsigned events;
static _Thread_local unsigned depth;
static void append(const char *path, const char *data, size_t size) {
    int fd = open(path, O_WRONLY|O_APPEND|O_CREAT|O_CLOEXEC, 0600);
    if (fd < 0 || write(fd, data, size) != (ssize_t)size) _exit(90);
    close(fd);
}
static void record(const char *op, FT_Face face, unsigned long a, long b, int error) {
    if (!face || !face->family_name || !strstr(face->family_name, "_CNKI")) return;
    unsigned event = atomic_fetch_add(&events, 1);
    if (event >= 100000) {
        if (event == 100000) append(FT_OBSERVE_DIRECTORY "/ft-limit", "event limit\n", 12);
        return;
    }
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) _exit(90);
    char line[512];
    int n = snprintf(line, sizeof(line), "%u\t%lld\t%ld\t%ld\t%s\t%p\t%.80s\t%lu\t%ld\t%d\t%u\t%u\t%u\n", event,
        (long long)now.tv_sec*1000000000LL+now.tv_nsec, (long)getpid(), syscall(SYS_gettid), op,
        (void*)face, face->family_name, a, b, error,
        face->size ? face->size->metrics.x_ppem : 0, face->size ? face->size->metrics.y_ppem : 0, depth);
    if (n <= 0 || (size_t)n >= sizeof(line)) _exit(90);
    append(FT_OBSERVE_DIRECTORY "/ft-events.tsv", line, (size_t)n);
}
FT_UInt FT_Get_Char_Index(FT_Face face, FT_ULong code) {
    FT_UInt (*next)(FT_Face,FT_ULong) = dlsym(RTLD_NEXT, "FT_Get_Char_Index");
    if (!next) _exit(91);
    ++depth;
    FT_UInt glyph = next(face, code);
    --depth;
    record("cmap", face, code, glyph, 0);
    return glyph;
}
FT_Error FT_Load_Glyph(FT_Face face, FT_UInt glyph, FT_Int32 flags) {
    FT_Error (*next)(FT_Face,FT_UInt,FT_Int32) = dlsym(RTLD_NEXT, "FT_Load_Glyph");
    if (!next) _exit(91);
    ++depth;
    FT_Error error = next(face, glyph, flags);
    --depth;
    record("load", face, glyph, flags, error);
    return error;
}
