// SPDX-License-Identifier: MIT
// Original public-API caller. No viewer, document, font or external image input.
#include <QCryptographicHash>
#include <algorithm>
#include <array>
#include <cerrno>
#include <cfenv>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <jpeglib.h>
#include <vector>

void create(jpeg_compress_struct &c, jpeg_error_mgr &error) {
    c.err = jpeg_std_error(&error); jpeg_create_compress(&c);
}

int main(int argc, char **argv) {
    if (argc < 2) return 2;
    const char *mode = argv[1];
    if (!std::strcmp(mode,"encodedlimit")) {
        jpeg_decompress_struct d{}; jpeg_error_mgr e{}; d.err = jpeg_std_error(&e);
        jpeg_create_decompress(&d);
        std::vector<unsigned char> input(16*1024*1024+1,0);
        jpeg_mem_src(&d,input.data(),input.size()); jpeg_destroy_decompress(&d); return 0;
    }
    if (!std::strcmp(mode, "events")) {
        for (int n = 0; n < 5002; ++n) {
            jpeg_compress_struct c{}; jpeg_error_mgr e{}; create(c,e); jpeg_destroy_compress(&c);
        }
        return 0;
    }
    if (!std::strcmp(mode, "contexts")) {
        std::array<jpeg_compress_struct,17> c{}; std::array<jpeg_error_mgr,17> e{};
        for (unsigned i = 0; i < c.size(); ++i) create(c[i],e[i]);
        for (auto &codec : c) jpeg_destroy_compress(&codec);
        return 0;
    }
    jpeg_compress_struct c{}; jpeg_error_mgr error{}; create(c,error);
    unsigned char *encoded = nullptr; unsigned long encoded_size = 0;
    jpeg_mem_dest(&c,&encoded,&encoded_size);
    c.image_width = 201; c.image_height = 101;
    c.input_components = 3; c.in_color_space = JCS_RGB;
    if (!std::strcmp(mode,"small")) { c.image_width = 32; c.image_height = 16; }
    if (!std::strcmp(mode,"gray")) { c.input_components = 1; c.in_color_space = JCS_GRAYSCALE; }
    if (!std::strcmp(mode,"wide")) c.image_width = 4097;
    if (!std::strcmp(mode,"pixels")) { c.image_width = 4000; c.image_height = 2000; }
    jpeg_set_defaults(&c); jpeg_set_quality(&c,100,TRUE); c.dct_method = JDCT_ISLOW;
    errno = EDOM; std::feclearexcept(FE_ALL_EXCEPT); std::feraiseexcept(FE_DIVBYZERO);
    jpeg_start_compress(&c,TRUE);
    if (!std::strcmp(mode,"wide") || !std::strcmp(mode,"pixels")) {
        jpeg_abort_compress(&c); jpeg_destroy_compress(&c); std::free(encoded); return 0;
    }
    const unsigned width = c.image_width, height = c.image_height, components = c.input_components;
    const unsigned stride = width*components+7;
    std::vector<unsigned char> input(stride*3,0xee);
    QCryptographicHash input_hash(QCryptographicHash::Sha256);
    while (c.next_scanline < height) {
        const unsigned count = std::min(3U,height-c.next_scanline);
        std::array<JSAMPROW,3> rows{};
        for (unsigned n = 0; n < count; ++n) {
            const unsigned y = c.next_scanline+n; rows[n] = input.data()+stride*n;
            for (unsigned x = 0; x < width; ++x) {
                rows[n][components*x] = (x*7+y*19)%256;
                if (components == 3) { rows[n][3*x+1] = (x*3+y*11)%256; rows[n][3*x+2] = (x*13+y*5)%256; }
                if (!std::strncmp(mode,"lossy-",6)) {
                    rows[n][3*x] = rows[n][3*x+1] = rows[n][3*x+2] = 64;
                    if (!std::strcmp(mode,"lossy-one") && x==1 && y==1) rows[n][3*x] = 65;
                }
            }
            input_hash.addData(reinterpret_cast<char *>(rows[n]),width*components);
        }
        if (jpeg_write_scanlines(&c,rows.data(),count) != count) return 3;
    }
    jpeg_finish_compress(&c);
    const int encoded_errno = errno, encoded_flags = std::fetestexcept(FE_ALL_EXCEPT);
    jpeg_destroy_compress(&c);
    if (argc == 3) {
        auto file = std::fopen(argv[2],"wb");
        if (!file || std::fwrite(encoded,1,encoded_size,file) != encoded_size || std::fclose(file)) return 4;
    }
    jpeg_decompress_struct d{}; jpeg_error_mgr de{}; d.err = jpeg_std_error(&de);
    jpeg_create_decompress(&d); jpeg_mem_src(&d,encoded,encoded_size);
    if (jpeg_read_header(&d,TRUE) != JPEG_HEADER_OK) return 5;
    d.out_color_space = JCS_RGB; d.dct_method = JDCT_ISLOW;
    if (!jpeg_start_decompress(&d)) return 6;
    std::vector<unsigned char> decoded((width*3+11)*2,0xdd);
    QCryptographicHash decoded_hash(QCryptographicHash::Sha256);
    while (d.output_scanline < height) {
        std::array<JSAMPROW,2> rows{decoded.data(),decoded.data()+width*3+11};
        const unsigned count = jpeg_read_scanlines(&d,rows.data(),2);
        if (!count) return 7;
        for (unsigned n = 0; n < count; ++n) decoded_hash.addData(reinterpret_cast<char *>(rows[n]),width*3);
        if (!std::strcmp(mode,"partial")) break;
    }
    if (std::strcmp(mode,"no-finish") && std::strcmp(mode,"partial") && !jpeg_finish_decompress(&d)) return 8;
    jpeg_destroy_decompress(&d); std::free(encoded);
    std::printf("%s\t%s\t%d\t%d\n",input_hash.result().toHex().constData(),
                decoded_hash.result().toHex().constData(),encoded_errno,encoded_flags);
    return 0;
}
