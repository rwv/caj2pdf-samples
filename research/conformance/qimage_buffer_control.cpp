// SPDX-License-Identifier: MIT
// Original public-API inputs, no viewer or corpus dependency.
#include <QImage>
#include <array>
#include <cstring>
#include <vector>

namespace {
void done(void *info) { ++*static_cast<int *>(info); }
void fill(uchar *data, int stride) {
    for (int y = 0; y < 101; ++y) for (int x = 0; x < 201; ++x) {
        data[y*stride+x*3] = uchar((x*17+y)%256);
        data[y*stride+x*3+1] = uchar((x+y*13)%256);
        data[y*stride+x*3+2] = uchar((x*3+y*5)%256);
    }
}
}

int main(int argc, char **argv) {
    alignas(64) std::array<uchar, 65536> tight, padded;
    tight.fill(0xac);
    padded.fill(0xbd);
    fill(tight.data(), 604);
    fill(padded.data(), 608);
    if (argc == 2 && std::strcmp(argv[1], "limit") == 0) {
        for (int i = 0; i < 10010; ++i) {
            QImage image(tight.data(), 1, 1, QImage::Format_RGB32);
            if (image.isNull()) return 1;
        }
        return 0;
    }
    int count = 0;
    {
        QImage a(tight.data(), 201, 101, QImage::Format_RGB888, done, &count);
        QImage b(static_cast<const uchar *>(tight.data()), 201, 101, QImage::Format_RGB888, done, &count);
        QImage c(padded.data(), 201, 101, 608, QImage::Format_RGB888, done, &count);
        QImage d(static_cast<const uchar *>(padded.data()), 201, 101, 608, QImage::Format_RGB888, done, &count);
        for (const auto *image : {&a, &b, &c, &d}) {
            if (image->width() != 201 || image->height() != 101
                || image->pixel(200, 100) != qRgb(172, 220, 76)) return 2;
        }
        // Observation must not detach a caller-owned buffer or consume cleanup.
        if (a.constBits() != tight.data() || b.constBits() != tight.data()
            || c.constBits() != padded.data() || d.constBits() != padded.data() || count != 0) return 3;
        if (a.bytesPerLine() != 604 || b.bytesPerLine() != 604
            || c.bytesPerLine() != 608 || d.bytesPerLine() != 608) return 4;
    }
    if (count != 4) return 5;
    QImage small(tight.data(), 32, 24, QImage::Format_RGB32);
    std::array<QRgb, 201*101> other_pixels{};
    QImage other_format(reinterpret_cast<uchar *>(other_pixels.data()), 201, 101, QImage::Format_RGB32);
    QImage invalid(tight.data(), -1, 24, QImage::Format_RGB32);
    QImage narrow(tight.data(), 199, 101, 604, QImage::Format_RGB888);
    QImage short_image(tight.data(), 201, 99, 604, QImage::Format_RGB888);
    std::vector<uchar> large(4096*1025*3, 0x31);
    QImage oversized(large.data(), 4096, 1025, QImage::Format_RGB888);
    return !invalid.isNull() || small.isNull() || other_format.isNull() || narrow.isNull()
        || short_image.isNull() || oversized.isNull() ? 6 : 0;
}
