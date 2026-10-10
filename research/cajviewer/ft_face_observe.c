// SPDX-License-Identifier: MIT
// Hash inputs to public FreeType face constructors; never export font bytes.
#define _GNU_SOURCE
#include <ft2build.h>
#include FT_FREETYPE_H
#include <dlfcn.h>
#include <fcntl.h>
#include <openssl/evp.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#ifndef FT_OBSERVE_DIRECTORY
#define FT_OBSERVE_DIRECTORY "/output"
#endif
#define FONT_LIMIT (32UL * 1024 * 1024)
#define FACE_EVENT_LIMIT 2000
static _Atomic unsigned events;
static _Thread_local unsigned depth;

static void append(const char *path, const char *data, size_t size) {
    int fd = open(path, O_WRONLY | O_APPEND | O_CREAT | O_CLOEXEC, 0600);
    if (fd < 0 || write(fd, data, size) != (ssize_t)size) _exit(90);
    close(fd);
}

static int selected(FT_Face face, char family[81]) {
    if (!face || !face->family_name || !strstr(face->family_name, "_CNKI")) return 0;
    size_t n = strnlen(face->family_name, 81);
    if (n > 80) _exit(90);
    for (size_t i = 0; i < n; ++i)
        if ((unsigned char)face->family_name[i] < 32 || (unsigned char)face->family_name[i] > 126) _exit(90);
    memcpy(family, face->family_name, n + 1);
    return 1;
}

static int hash_input(const void *memory, long size, const char *path,
                      char digest[65], unsigned long *bytes) {
    EVP_MD_CTX *context = EVP_MD_CTX_new();
    if (!context || !EVP_DigestInit_ex(context, EVP_sha256(), NULL)) _exit(90);
    int ok = 0;
    if (memory && size > 0 && (unsigned long)size <= FONT_LIMIT) {
        *bytes = (unsigned long)size;
        ok = EVP_DigestUpdate(context, memory, (size_t)size);
    } else if (path) {
        int fd = open(path, O_RDONLY | O_CLOEXEC);
        struct stat before, after;
        if (fd >= 0 && !fstat(fd, &before) && S_ISREG(before.st_mode)
                && before.st_size > 0 && (unsigned long)before.st_size <= FONT_LIMIT) {
            unsigned char buffer[65536];
            *bytes = 0; ok = 1;
            while (*bytes < (unsigned long)before.st_size) {
                size_t wanted = (unsigned long)before.st_size - *bytes;
                if (wanted > sizeof(buffer)) wanted = sizeof(buffer);
                ssize_t got = read(fd, buffer, wanted);
                if (got <= 0 || !EVP_DigestUpdate(context, buffer, (size_t)got)) { ok = 0; break; }
                *bytes += (unsigned long)got;
            }
            if (fstat(fd, &after) || before.st_size != after.st_size
                    || before.st_mtim.tv_sec != after.st_mtim.tv_sec
                    || before.st_mtim.tv_nsec != after.st_mtim.tv_nsec) ok = 0;
        }
        if (fd >= 0) close(fd);
    }
    unsigned char result[32]; unsigned length = 0;
    if (ok && (!EVP_DigestFinal_ex(context, result, &length) || length != 32)) _exit(90);
    EVP_MD_CTX_free(context);
    if (!ok) { strcpy(digest, "unmeasured"); return 0; }
    for (unsigned i = 0; i < 32; ++i) snprintf(digest + i * 2, 3, "%02x", result[i]);
    return 1;
}

static void record(const char *operation, const char *family, uintptr_t face,
                   long index, int error, const char *kind, unsigned long bytes,
                   const char *digest, const char *path) {
    unsigned event = atomic_fetch_add(&events, 1);
    if (event >= FACE_EVENT_LIMIT) {
        if (event == FACE_EVENT_LIMIT) append(FT_OBSERVE_DIRECTORY "/ft-face-limit", "event limit\n", 12);
        return;
    }
    char path_hex[1025] = "-";
    if (path) {
        size_t n = strnlen(path, 513);
        if (n > 512) strcpy(path_hex, "unmeasured");
        else for (size_t i = 0; i < n; ++i) snprintf(path_hex + i * 2, 3, "%02x", (unsigned char)path[i]);
    }
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now)) _exit(90);
    char line[1536];
    int n = snprintf(line, sizeof(line), "%u\t%lld\t%ld\t%ld\t%s\t0x%lx\t%s\t%ld\t%d\t%s\t%lu\t%s\t%s\n",
        event, (long long)now.tv_sec * 1000000000LL + now.tv_nsec,
        (long)getpid(), syscall(SYS_gettid), operation, (unsigned long)face,
        family, index, error, kind, bytes, digest, path_hex);
    if (n <= 0 || (size_t)n >= sizeof(line)) _exit(90);
    append(FT_OBSERVE_DIRECTORY "/ft-faces.tsv", line, (size_t)n);
}

static void opened(FT_Face *output, int error, long index, const void *memory,
                   long size, const char *path, const char *kind) {
    if (depth || error || index < 0 || !output) return;
    char family[81];
    if (!selected(*output, family)) return;
    char digest[65]; unsigned long bytes = 0;
    hash_input(memory, size, path, digest, &bytes);
    record("open", family, (uintptr_t)*output, index, 0, kind, bytes, digest, path);
}

FT_Error FT_New_Face(FT_Library library, const char *path, FT_Long index, FT_Face *output) {
    FT_Error (*next)(FT_Library, const char *, FT_Long, FT_Face *) = dlsym(RTLD_NEXT, "FT_New_Face");
    if (!next) _exit(91);
    ++depth; FT_Error error = next(library, path, index, output); --depth;
    opened(output, error, index, NULL, 0, path, "file");
    return error;
}

FT_Error FT_New_Memory_Face(FT_Library library, const FT_Byte *memory, FT_Long size,
                           FT_Long index, FT_Face *output) {
    FT_Error (*next)(FT_Library, const FT_Byte *, FT_Long, FT_Long, FT_Face *) = dlsym(RTLD_NEXT, "FT_New_Memory_Face");
    if (!next) _exit(91);
    ++depth; FT_Error error = next(library, memory, size, index, output); --depth;
    opened(output, error, index, memory, size, NULL, "memory");
    return error;
}

FT_Error FT_Open_Face(FT_Library library, const FT_Open_Args *args, FT_Long index, FT_Face *output) {
    FT_Error (*next)(FT_Library, const FT_Open_Args *, FT_Long, FT_Face *) = dlsym(RTLD_NEXT, "FT_Open_Face");
    if (!next) _exit(91);
    ++depth; FT_Error error = next(library, args, index, output); --depth;
    if (!depth && !error && args) {
        unsigned source = args->flags & (FT_OPEN_MEMORY | FT_OPEN_PATHNAME | FT_OPEN_STREAM);
        if (source == FT_OPEN_MEMORY) opened(output, error, index, args->memory_base, args->memory_size, NULL, "memory");
        else if (source == FT_OPEN_PATHNAME) opened(output, error, index, NULL, 0, args->pathname, "file");
        else opened(output, error, index, NULL, 0, NULL, "opaque-stream");
    }
    return error;
}

FT_Error FT_Reference_Face(FT_Face face) {
    FT_Error (*next)(FT_Face) = dlsym(RTLD_NEXT, "FT_Reference_Face");
    if (!next) _exit(91);
    char family[81]; int observe = !depth && selected(face, family);
    long index = observe ? face->face_index : 0;
    ++depth; FT_Error error = next(face); --depth;
    if (observe) record("reference", family, (uintptr_t)face, index, error, "-", 0, "-", NULL);
    return error;
}

FT_Error FT_Done_Face(FT_Face face) {
    FT_Error (*next)(FT_Face) = dlsym(RTLD_NEXT, "FT_Done_Face");
    if (!next) _exit(91);
    char family[81]; int observe = !depth && selected(face, family);
    long index = observe ? face->face_index : 0;
    uintptr_t identity = (uintptr_t)face;
    ++depth; FT_Error error = next(face); --depth;
    if (observe) record("done", family, identity, index, error, "-", 0, "-", NULL);
    return error;
}
