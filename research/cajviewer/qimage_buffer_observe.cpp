// SPDX-License-Identifier: MIT
// Original public Qt5 buffer observation; Linux x86-64 ABI only.
// Forward first, then hash selected RGB888 rows without padding or image copies.
// No document text, font program, or raster bytes are exported.
// Floating state is sampled at this boundary, not during earlier rendering.
// LIMIT means incomplete observation. Use only in an offline contained process.
#include <QCryptographicHash>
#include <QImage>
#include <atomic>
#include <cfenv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#include <xmmintrin.h>

#if !defined(__linux__) || !defined(__x86_64__) || QT_VERSION < QT_VERSION_CHECK(5, 0, 0) || QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
#error "This research observer requires Linux x86-64 and Qt5"
#endif
#ifndef QIMAGE_OBSERVE_OUTPUT
#define QIMAGE_OBSERVE_OUTPUT "/output/buffers.tsv"
#endif

namespace {
std::atomic<unsigned> sequence{0};

template<class Function> Function next(const char *symbol) {
    auto address = dlsym(RTLD_NEXT, symbol);
    if (!address) _exit(125);
    return reinterpret_cast<Function>(address);
}

void record(const char *kind, const QImage *image, const void *data) {
    // Saturate instead of eventually wrapping and reopening the log budget.
    unsigned n = sequence.load();
    do {
        if (n > 10000) return;
    } while (!sequence.compare_exchange_weak(n, n+1));
    const int rounding = std::fegetround();
    const unsigned mxcsr = _mm_getcsr();
    unsigned short x87;
    asm volatile ("fnstcw %0" : "=m"(x87));
    char rgb[65] = {};
    const auto pixels = static_cast<unsigned long long>(image->width()) * image->height();
    if (n < 10000 && image->format() == QImage::Format_RGB888
        && image->width() >= 200 && image->height() >= 100 && pixels <= 4*1024*1024
        && image->bytesPerLine() >= image->width()*3) {
        QCryptographicHash hash(QCryptographicHash::Sha256);
        for (int y = 0; y < image->height(); ++y) {
            hash.addData(reinterpret_cast<const char *>(image->constScanLine(y)), image->width()*3);
        }
        const auto digest = hash.result().toHex();
        if (digest.size() != 64) _exit(126);
        std::memcpy(rgb, digest.constData(), 64);
    }
    timespec time{};
    if (clock_gettime(CLOCK_MONOTONIC, &time)) _exit(126);
    const auto ns = static_cast<unsigned long long>(time.tv_sec)*1000000000ULL + time.tv_nsec;
    char line[512];
    const int size = n == 10000 ? std::snprintf(line, sizeof(line), "LIMIT\n") :
        std::snprintf(line, sizeof(line), "%u\t%llu\t%ld\t%s\t%d\t%d\t%d\t%d\t%llx\t%u\t%d\t%x\t%x\t%s\n",
            n, ns, static_cast<long>(syscall(SYS_gettid)), kind,
            image->width(), image->height(), int(image->format()), image->bytesPerLine(),
            static_cast<unsigned long long>(image->cacheKey()),
            unsigned(reinterpret_cast<uintptr_t>(data)&63), rounding, mxcsr, unsigned(x87), rgb);
    if (size <= 0 || size >= int(sizeof(line))) _exit(126);
    const int fd = open(QIMAGE_OBSERVE_OUTPUT, O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC, 0600);
    if (fd < 0) _exit(126);
    const auto wrote = write(fd, line, size);
    close(fd);
    if (wrote != size) _exit(126);
}
}

// Public Qt5 signatures; ABI names from compiling our own four-call object.
#define WRAP_TIGHT(NAME, TYPE, SYMBOL) \
extern "C" void NAME(QImage *, TYPE, int, int, QImage::Format, QImageCleanupFunction, void *) asm(SYMBOL); \
extern "C" void NAME(QImage *self, TYPE data, int w, int h, QImage::Format fmt, QImageCleanupFunction done, void *info) { \
    using Function = void(*)(QImage *, TYPE, int, int, QImage::Format, QImageCleanupFunction, void *); \
    static auto original = next<Function>(SYMBOL); \
    original(self, data, w, h, fmt, done, info); \
    record(#NAME, self, data); \
}
#define WRAP_STRIDE(NAME, TYPE, SYMBOL) \
extern "C" void NAME(QImage *, TYPE, int, int, int, QImage::Format, QImageCleanupFunction, void *) asm(SYMBOL); \
extern "C" void NAME(QImage *self, TYPE data, int w, int h, int stride, QImage::Format fmt, QImageCleanupFunction done, void *info) { \
    using Function = void(*)(QImage *, TYPE, int, int, int, QImage::Format, QImageCleanupFunction, void *); \
    static auto original = next<Function>(SYMBOL); \
    original(self, data, w, h, stride, fmt, done, info); \
    record(#NAME, self, data); \
}
WRAP_TIGHT(mutable_tight, uchar *, "_ZN6QImageC1EPhiiNS_6FormatEPFvPvES2_")
WRAP_TIGHT(const_tight, const uchar *, "_ZN6QImageC1EPKhiiNS_6FormatEPFvPvES3_")
WRAP_STRIDE(mutable_stride, uchar *, "_ZN6QImageC1EPhiiiNS_6FormatEPFvPvES2_")
WRAP_STRIDE(const_stride, const uchar *, "_ZN6QImageC1EPKhiiiNS_6FormatEPFvPvES3_")
