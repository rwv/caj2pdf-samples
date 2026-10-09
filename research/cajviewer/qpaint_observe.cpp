// SPDX-License-Identifier: MIT
// Original observation of documented Qt painting calls. Geometry metadata and
// bounded finished-page pixmaps stay external. No vendor implementation, text
// extraction or font outlines are inspected.
#include <QPainter>
#include <QPixmap>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <fcntl.h>
#include <mutex>
#include <unistd.h>

namespace {
std::atomic<unsigned> sequence{0};
thread_local unsigned depth = 0;
std::mutex capture_mutex;
qint64 captured[128] = {};
unsigned capture_count = 0;
unsigned long long capture_pixels = 0;

void capture(const QPixmap &pixmap) {
    if (pixmap.width() < 200 || pixmap.height() < 100) return;
    std::lock_guard<std::mutex> lock(capture_mutex);
    const qint64 key = pixmap.cacheKey();
    for (unsigned i = 0; i < capture_count; ++i) if (captured[i] == key) return;
    const auto pixels = static_cast<unsigned long long>(pixmap.width()) * pixmap.height();
    if (pixels > 4*1024*1024 || capture_pixels+pixels > 64*1024*1024 || capture_count == 128) {
        int fd = open("/output/capture-limit", O_WRONLY|O_CREAT|O_CLOEXEC, 0600);
        if (fd < 0) _exit(126);
        close(fd);
        return; // A limit makes the observation incomplete, never a pass.
    }
    char path[160];
    std::snprintf(path, sizeof(path), "/output/pixmap-%ld-%016llx.png",
                  static_cast<long>(getpid()), static_cast<unsigned long long>(key));
    // This is the complete public raster passed for display, equivalent in
    // provenance to a screenshot; it is not a recovered vector/font program.
    if (!pixmap.save(QString::fromLatin1(path), "PNG")) _exit(126);
    captured[capture_count++] = key;
    capture_pixels += pixels;
}

template <typename Function> Function next(const char *symbol) {
    void *address = dlsym(RTLD_NEXT, symbol);
    if (!address) _exit(125); // A missing hook cannot silently alter the viewer.
    return reinterpret_cast<Function>(address);
}

void record(const char *kind, QPainter *painter, const QRectF &target,
            const QRectF &source, int width, int height, long long identity) {
    const unsigned number = sequence.fetch_add(1);
    if (number > 100000) return;
    char line[1024];
    int length;
    if (number == 100000) {
        length = std::snprintf(line, sizeof(line), "LIMIT\n");
    } else {
        const auto transform = painter->combinedTransform();
        const auto clip = painter->clipBoundingRect();
        const auto *device = painter->device();
        length = std::snprintf(line, sizeof(line),
            "%u\t%s\t%p\t%d\t%d\t%d\t%lld\t%d\t%d\t"
            "%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t"
            "%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t%.12g\t"
            "%d\t%.12g\t%d\t%.12g\t%.12g\t%.12g\t%.12g\t%d\n",
            number, kind, static_cast<const void *>(device),
            device ? device->devType() : -1, device ? device->width() : -1,
            device ? device->height() : -1, identity, width, height,
            target.x(), target.y(), target.width(), target.height(),
            source.x(), source.y(), source.width(), source.height(),
            transform.m11(), transform.m12(), transform.m21(), transform.m22(),
            transform.dx(), transform.dy(), static_cast<int>(painter->compositionMode()),
            painter->opacity(), painter->hasClipping(),
            clip.x(), clip.y(), clip.width(), clip.height(), transform.isAffine());
    }
    if (length <= 0 || length >= static_cast<int>(sizeof(line))) _exit(126);
    int fd = open("/output/paint.tsv", O_WRONLY | O_APPEND | O_CREAT | O_CLOEXEC, 0600);
    if (fd < 0) _exit(126);
    const auto written = write(fd, line, static_cast<size_t>(length));
    close(fd);
    if (written != length) _exit(126);
}

struct Call {
    bool outer = depth++ == 0;
    ~Call() { --depth; }
};
}

void QPainter::drawPixmap(const QRectF &target, const QPixmap &pixmap, const QRectF &source) {
    using Function = void (*)(QPainter *, const QRectF &, const QPixmap &, const QRectF &);
    static auto original = next<Function>("_ZN8QPainter10drawPixmapERK6QRectFRK7QPixmapS2_");
    Call call;
    if (call.outer) {
        record("pixmap-rect", this, target, source, pixmap.width(), pixmap.height(), pixmap.cacheKey());
        capture(pixmap);
    }
    original(this, target, pixmap, source);
}

void QPainter::drawPixmap(const QPointF &point, const QPixmap &pixmap) {
    using Function = void (*)(QPainter *, const QPointF &, const QPixmap &);
    static auto original = next<Function>("_ZN8QPainter10drawPixmapERK7QPointFRK7QPixmap");
    Call call;
    if (call.outer) {
        record("pixmap-point", this, QRectF(point, pixmap.size()),
               QRectF(QPointF(), pixmap.size()), pixmap.width(), pixmap.height(), pixmap.cacheKey());
        capture(pixmap);
    }
    original(this, point, pixmap);
}
