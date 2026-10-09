// SPDX-License-Identifier: MIT
// Original public Qt model/view observation. Counts only; no item text/fonts.
#include <QApplication>
#include <QAbstractItemModel>
#include <QCryptographicHash>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QLabel>
#include <QLineEdit>
#include <QTimer>
#include <QTreeView>
#include <dlfcn.h>
#include <fcntl.h>
#include <time.h>
#include <unistd.h>

#if !defined(__linux__) || !defined(__x86_64__) || QT_VERSION < QT_VERSION_CHECK(5, 0, 0) || QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
#error "This observer requires Linux x86-64 and Qt5"
#endif
#ifndef TREE_OBSERVE_OUTPUT
#define TREE_OBSERVE_OUTPUT "/output/trees.jsonl"
#endif
#ifndef TREE_OBSERVE_STOP
#define TREE_OBSERVE_STOP "/output/stop-observer"
#endif

namespace {
struct Counts {
    int nodes = 0;
    int depth = 0;
    bool pending = false;
    bool limit = false;
    bool invalid = false;
};

void visit(const QAbstractItemModel *model, const QModelIndex &parent, int depth, Counts &out) {
    out.pending = out.pending || model->canFetchMore(parent);
    const int rows = model->rowCount(parent);
    if (rows < 0) { out.invalid = true; return; }
    if (rows > 10000 - out.nodes || (rows && depth > 128)) { out.limit = true; return; }
    for (int row = 0; row < rows; ++row) {
        if (out.nodes == 10000) { out.limit = true; return; }
        const auto index = model->index(row, 0, parent);
        if (!index.isValid()) { out.invalid = true; return; }
        ++out.nodes;
        if (depth > out.depth) out.depth = depth;
        visit(model, index, depth + 1, out);
        if (out.limit || out.invalid) return;
    }
}

void write(const QJsonObject &object) {
    auto entry = object;
    entry["pid"] = int(getpid());
    const auto bytes = QJsonDocument(entry).toJson(QJsonDocument::Compact) + '\n';
    if (bytes.size() > 2048) _exit(126);
    int fd = open(TREE_OBSERVE_OUTPUT, O_WRONLY|O_CREAT|O_APPEND|O_CLOEXEC, 0600);
    if (fd < 0) _exit(126);
    const auto count = ::write(fd, bytes.constData(), bytes.size());
    close(fd);
    if (count != bytes.size()) _exit(126);
}

void observe(unsigned tick) {
    const auto widgets = QApplication::allWidgets();
    if (widgets.size() > 8192) { write({{"tick", int(tick)}, {"widget_limit", true}}); return; }
    timespec now{};
    if (clock_gettime(CLOCK_MONOTONIC, &now)) _exit(126);
    const QString stamp = QString::number(static_cast<qulonglong>(now.tv_sec)*1000000000ULL + now.tv_nsec);
    unsigned trees = 0;
    QJsonArray page_fields;
    int empty_labels = 0;
    for (auto *widget : widgets) {
        if (widget->isVisible()) {
            const auto pos = widget->mapToGlobal(QPoint());
            if (widget->inherits("QLineEdit") && pos.y() >= 0 && pos.y() < 150) {
                const auto value = static_cast<QLineEdit *>(widget)->text();
                if (value.size() < 24 && value.count('/') == 1) {
                    const auto parts = value.split('/');
                    bool a = false, b = false;
                    const int current = parts[0].toInt(&a), total = parts[1].toInt(&b);
                    if (a && b && current > 0 && current <= total && total <= 1000000)
                        page_fields.append(QJsonObject{{"current", current}, {"total", total},
                                                       {"x", pos.x()}, {"y", pos.y()}});
                }
            }
            if (widget->inherits("QLabel") && pos.x() >= 60 && pos.x() < 790
                && pos.y() >= 150 && pos.y() < 1180
                && static_cast<QLabel *>(widget)->text() == QString::fromUtf8("暂无目录")) ++empty_labels;
        }
        if (!widget->inherits("QTreeView")) continue;
        if (++trees > 64) { write({{"tick", int(tick)}, {"tree_limit", true}}); break; }
        const auto *view = static_cast<QTreeView *>(widget);
        const auto *model = view->model();
        const auto root = view->rootIndex();
        const auto pos = view->mapToGlobal(QPoint());
        Counts count;
        if (model) visit(model, root, 1, count);
        const auto name = view->objectName().toUtf8();
        if (name.size() > 1024) { write({{"tick", int(tick)}, {"name_limit", true}}); continue; }
        write({{"tick", int(tick)}, {"monotonic_ns", stamp},
               {"view", QString::number(reinterpret_cast<quintptr>(view), 16)},
               {"class", QString::fromLatin1(view->metaObject()->className())},
               {"name_sha256", QString::fromLatin1(QCryptographicHash::hash(name, QCryptographicHash::Sha256).toHex())},
               {"visible", view->isVisible()}, {"x", pos.x()}, {"y", pos.y()},
               {"width", view->width()}, {"height", view->height()},
               {"model", model ? QString::fromLatin1(model->metaObject()->className()) : QString()},
               {"model_present", model != nullptr}, {"root_valid", root.isValid()},
               {"root_rows", model ? model->rowCount(root) : -1},
               {"nodes", count.nodes}, {"depth", count.depth},
               {"can_fetch_more", count.pending}, {"limit", count.limit}, {"invalid", count.invalid}});
    }
    write({{"tick", int(tick)}, {"monotonic_ns", stamp}, {"sample_complete", trees <= 64},
           {"tree_count", int(trees)}, {"widget_count", widgets.size()},
           {"page_fields", page_fields}, {"empty_contents_labels", empty_labels}});
}

void start() {
    static bool started = false;
    if (started) return;
    started = true;
    auto *timer = new QTimer(QCoreApplication::instance());
    QObject::connect(timer, &QTimer::timeout, timer, [timer, tick = 0U]() mutable {
        if (access(TREE_OBSERVE_STOP, F_OK) == 0) {
            write({{"sampling_stopped", "requested"}, {"last_tick", int(tick)}});
            timer->stop();
            return;
        }
        observe(++tick);
        if (tick == 60) {
            write({{"sampling_stopped", "time_limit"}, {"last_tick", int(tick)}});
            timer->stop();
        }
    });
    timer->start(1000);
}

template<class Function> Function next(const char *name) {
    auto *address = dlsym(RTLD_NEXT, name);
    if (!address) _exit(125);
    return reinterpret_cast<Function>(address);
}
}

int QApplication::exec() {
    static auto original = next<int(*)()>("_ZN12QApplication4execEv");
    start();
    return original();
}

int QCoreApplication::exec() {
    static auto original = next<int(*)()>("_ZN16QCoreApplication4execEv");
    start();
    return original();
}
