// SPDX-License-Identifier: MIT
// Original pass-through observation of public libjpeg APIs, not renderer internals.
// Hash accepted RGB scanlines only. LIMIT/UNSUPPORTED invalidate completeness.
#include <QCryptographicHash>
#include <array>
#include <atomic>
#include <cerrno>
#include <cfenv>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fcntl.h>
#include <jpeglib.h>
#include <mutex>
#include <sys/syscall.h>
#include <time.h>
#include <type_traits>
#include <unistd.h>

#ifndef JPEG_OBSERVE_OUTPUT
#define JPEG_OBSERVE_OUTPUT "/output/jpeg.tsv"
#endif

namespace {
constexpr unsigned MAX_EVENTS = 10000, MAX_CONTEXTS = 16;
struct Context {
    void *owner = nullptr;
    bool compressor = false, eligible = false, active = false;
    unsigned width = 0, height = 0, rows = 0;
    int components = 0, color = 0, quality = -1, dct = -1, unit_quantizers = 0;
    unsigned sampling = 0;
    unsigned serial = 0;
    unsigned char **encoded_data = nullptr;
    unsigned long *encoded_size = nullptr;
    char encoded_sha256[65] = {};
    QCryptographicHash hash{QCryptographicHash::Sha256};
};
std::mutex mutex;
std::atomic<unsigned> event{0};
unsigned serial = 0;

std::array<Context, MAX_CONTEXTS> &contexts() {
    // LD_PRELOAD also reaches the launcher shell, which has not loaded Qt.
    // Construct Qt hash objects only when the target calls the observed API.
    static std::array<Context, MAX_CONTEXTS> value;
    return value;
}

// Hashing/logging must not leak errno or floating-point exception state.
struct State {
    int error = errno;
    fenv_t floating;
    State() { if (fegetenv(&floating)) _exit(126); }
    ~State() { if (fesetenv(&floating)) _exit(126); errno = error; }
};

template<class F> F next(const char *name) {
    const int saved = errno;
    auto address = dlsym(RTLD_NEXT, name);
    errno = saved;
    if (!address) _exit(125);
    return reinterpret_cast<F>(address);
}

void log(const char *kind, const Context *c = nullptr, const char *hash = "") {
    unsigned n = event.load();
    do { if (n > MAX_EVENTS) return; } while (!event.compare_exchange_weak(n, n+1));
    timespec now{};
    if (clock_gettime(CLOCK_MONOTONIC, &now)) _exit(126);
    char line[512];
    const auto ns = static_cast<unsigned long long>(now.tv_sec)*1000000000ULL + now.tv_nsec;
    const int size = n == MAX_EVENTS ? std::snprintf(line, sizeof(line), "LIMIT_EVENTS\n") :
        std::snprintf(line, sizeof(line), "%u\t%llu\t%ld\t%s\t%u\t%d\t%u\t%u\t%u\t%d\t%d\t%d\t%d\t%x\t%d\t%s\t%s\t%ld\n",
          n, ns, static_cast<long>(syscall(SYS_gettid)), kind, c ? c->serial : 0,
          c ? int(c->compressor) : 0, c ? c->width : 0, c ? c->height : 0, c ? c->rows : 0,
          c ? c->components : 0, c ? c->color : 0, c ? c->quality : -1,
          c ? c->dct : -1, c ? c->sampling : 0, c ? c->unit_quantizers : 0, hash,
          c ? c->encoded_sha256 : "", static_cast<long>(getpid()));
    if (size <= 0 || size >= int(sizeof(line))) _exit(126);
    const int fd = open(JPEG_OBSERVE_OUTPUT, O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC, 0600);
    if (fd < 0) _exit(126);
    const auto wrote = write(fd, line, size);
    close(fd);
    if (wrote != size) _exit(126);
}

Context *find(void *owner) {
    for (auto &c : contexts()) if (c.owner == owner) return &c;
    return nullptr;
}

void create(void *owner, bool compressor, bool abi) {
    State state;
    std::lock_guard<std::mutex> lock(mutex);
    if (!abi) { log("UNSUPPORTED_ABI"); return; }
    if (find(owner)) { log("LIMIT_DUPLICATE_CONTEXT"); return; }
    for (auto &c : contexts()) if (!c.owner) {
        c.owner = owner; c.compressor = compressor; c.active = false; c.eligible = false;
        c.width = c.height = c.rows = 0; c.components = c.color = 0;
        c.quality = c.dct = -1; c.sampling = c.unit_quantizers = 0;
        c.encoded_data = nullptr; c.encoded_size = nullptr; c.encoded_sha256[0] = 0;
        c.serial = ++serial; c.hash.reset(); log("CREATE", &c); return;
    }
    log("LIMIT_CONTEXTS");
}

void encoded(Context *c, const unsigned char *data, unsigned long size) {
    c->encoded_sha256[0] = 0;
    if (!data || !size || size > 16*1024*1024) { log("UNSUPPORTED_ENCODED_SIZE", c); return; }
    QCryptographicHash hash(QCryptographicHash::Sha256);
    for (unsigned long offset = 0; offset < size;) {
        const auto count = size-offset > 65536 ? 65536 : size-offset;
        hash.addData(reinterpret_cast<const char *>(data+offset),int(count)); offset += count;
    }
    const auto digest = hash.result().toHex();
    if (digest.size() != 64) _exit(126);
    std::memcpy(c->encoded_sha256,digest.constData(),64); c->encoded_sha256[64] = 0;
}

template<class Codec> void begin(Codec *codec) {
    State state;
    std::lock_guard<std::mutex> lock(mutex);
    auto c = find(codec);
    if (!c) { log("UNSUPPORTED_UNTRACKED_START"); return; }
    // Do not dereference an untracked or incompatible public ABI layout.
    unsigned width, height;
    int components, color;
    if constexpr (std::is_same_v<Codec, jpeg_compress_struct>) {
        width = codec->image_width; height = codec->image_height;
        components = codec->input_components; color = int(codec->in_color_space);
    } else {
        width = codec->output_width; height = codec->output_height;
        components = codec->output_components; color = int(codec->out_color_space);
    }
    if (c->active) log("INCOMPLETE_RESTART", c);
    c->width = width; c->height = height; c->components = components; c->color = color;
    if (c->compressor) c->encoded_sha256[0] = 0;
    c->rows = 0; c->active = true; c->hash.reset(); c->dct = int(codec->dct_method);
    c->sampling = 0; c->unit_quantizers = 1;
    for (int i = 0; i < codec->num_components && i < 4; ++i) {
        const auto &component = codec->comp_info[i];
        c->sampling = (c->sampling << 8) | ((component.h_samp_factor & 15) << 4) | (component.v_samp_factor & 15);
        const int q = component.quant_tbl_no;
        if (q < 0 || q >= NUM_QUANT_TBLS || !codec->quant_tbl_ptrs[q]) { c->unit_quantizers = 0; continue; }
        for (int k = 0; k < DCTSIZE2; ++k) if (codec->quant_tbl_ptrs[q]->quantval[k] != 1) c->unit_quantizers = 0;
    }
    c->eligible = width >= 200 && height >= 100 && width <= 4096 && height <= 4096
        && static_cast<unsigned long long>(width)*height <= 4*1024*1024
        && components == 3 && color == JCS_RGB && BITS_IN_JSAMPLE == 8;
    log(c->eligible ? "START_RGB" : "UNSUPPORTED_GRID_OR_COLOR", c);
}

void rows(void *owner, JSAMPARRAY data, unsigned requested, unsigned accepted) {
    State state;
    std::lock_guard<std::mutex> lock(mutex);
    auto c = find(owner);
    if (!c || !c->active || !c->eligible) return;
    const auto next_row = c->compressor ? static_cast<j_compress_ptr>(owner)->next_scanline
                                       : static_cast<j_decompress_ptr>(owner)->output_scanline;
    if (accepted > requested || accepted > c->height-c->rows || next_row != c->rows+accepted || (!data && accepted)) {
        c->eligible = false; log("INCOMPLETE_ROWS", c); return;
    }
    for (unsigned i = 0; i < accepted; ++i) {
        if (!data[i]) { c->eligible = false; log("INCOMPLETE_NULL_ROW", c); return; }
        c->hash.addData(reinterpret_cast<const char *>(data[i]), int(c->width*3));
    }
    c->rows += accepted;
}

void completed_rows(Context *c, const char *complete_kind, const char *incomplete_kind) {
    const bool complete = c->active && c->eligible && c->rows == c->height;
    char rgb[65] = {};
    if (complete) {
        const auto digest = c->hash.result().toHex();
        if (digest.size() != 64) _exit(126);
        std::memcpy(rgb,digest.constData(),64);
    }
    if (c->compressor && c->encoded_data && c->encoded_size) encoded(c,*c->encoded_data,*c->encoded_size);
    log(complete ? complete_kind : incomplete_kind, c, rgb);
    c->active = false;
}

void finish(void *owner) {
    State state;
    std::lock_guard<std::mutex> lock(mutex);
    if (auto c = find(owner)) completed_rows(c,"FINISH_RGB","INCOMPLETE_FINISH");
    else log("UNSUPPORTED_UNTRACKED_FINISH");
}

void destroy(void *owner) {
    State state;
    std::lock_guard<std::mutex> lock(mutex);
    if (auto c = find(owner)) {
        // This confirms all returned RGB rows, not end-of-stream validation.
        // It must run before the public destroy call can free caller storage.
        if (c->active && !c->compressor) completed_rows(c,"RGB_ROWS_AT_DESTROY","INCOMPLETE_DESTROY");
        else log(c->active ? "INCOMPLETE_DESTROY" : "DESTROY", c);
        c->owner = nullptr; c->active = false;
    }
}
}

extern "C" void jpeg_CreateCompress(j_compress_ptr c, int version, size_t size) {
    static auto original = next<decltype(&jpeg_CreateCompress)>("jpeg_CreateCompress");
    original(c, version, size); create(c, true, version == JPEG_LIB_VERSION && size == sizeof(*c));
}
extern "C" void jpeg_CreateDecompress(j_decompress_ptr c, int version, size_t size) {
    static auto original = next<decltype(&jpeg_CreateDecompress)>("jpeg_CreateDecompress");
    original(c, version, size); create(c, false, version == JPEG_LIB_VERSION && size == sizeof(*c));
}
extern "C" void jpeg_set_quality(j_compress_ptr c, int quality, boolean baseline) {
    static auto original = next<decltype(&jpeg_set_quality)>("jpeg_set_quality"); original(c, quality, baseline);
    State state; std::lock_guard<std::mutex> lock(mutex);
    if (auto found = find(c)) found->quality = quality;
}
extern "C" void jpeg_mem_dest(j_compress_ptr c, unsigned char **data, unsigned long *size) {
    static auto original = next<decltype(&jpeg_mem_dest)>("jpeg_mem_dest"); original(c,data,size);
    State state; std::lock_guard<std::mutex> lock(mutex);
    if (auto found = find(c)) { found->encoded_data = data; found->encoded_size = size; }
}
extern "C" void jpeg_mem_src(j_decompress_ptr c, const unsigned char *data, unsigned long size) {
    static auto original = next<decltype(&jpeg_mem_src)>("jpeg_mem_src"); original(c,data,size);
    State state; std::lock_guard<std::mutex> lock(mutex);
    if (auto found = find(c)) encoded(found,data,size);
}
extern "C" void jpeg_start_compress(j_compress_ptr c, boolean tables) {
    static auto original = next<decltype(&jpeg_start_compress)>("jpeg_start_compress"); original(c, tables);
    begin(c);
}
extern "C" boolean jpeg_start_decompress(j_decompress_ptr c) {
    static auto original = next<decltype(&jpeg_start_decompress)>("jpeg_start_decompress"); const auto result = original(c);
    if (result) begin(c);
    return result;
}
extern "C" JDIMENSION jpeg_write_scanlines(j_compress_ptr c, JSAMPARRAY data, JDIMENSION count) {
    static auto original = next<decltype(&jpeg_write_scanlines)>("jpeg_write_scanlines"); const auto result = original(c, data, count);
    rows(c, data, count, result); return result;
}
extern "C" JDIMENSION jpeg_read_scanlines(j_decompress_ptr c, JSAMPARRAY data, JDIMENSION count) {
    static auto original = next<decltype(&jpeg_read_scanlines)>("jpeg_read_scanlines"); const auto result = original(c, data, count);
    rows(c, data, count, result); return result;
}
extern "C" void jpeg_finish_compress(j_compress_ptr c) {
    static auto original = next<decltype(&jpeg_finish_compress)>("jpeg_finish_compress"); original(c); finish(c);
}
extern "C" boolean jpeg_finish_decompress(j_decompress_ptr c) {
    static auto original = next<decltype(&jpeg_finish_decompress)>("jpeg_finish_decompress"); const auto result = original(c);
    if (result) finish(c);
    return result;
}
#define DESTROY(NAME, TYPE) \
extern "C" void NAME(TYPE c) { \
    static auto original = next<decltype(&NAME)>(#NAME); destroy(c); original(c); \
}
DESTROY(jpeg_destroy_compress, j_compress_ptr)
DESTROY(jpeg_destroy_decompress, j_decompress_ptr)
DESTROY(jpeg_destroy, j_common_ptr)
