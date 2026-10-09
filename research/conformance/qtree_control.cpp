// SPDX-License-Identifier: MIT
// Independent original models, no viewer, corpus, private roles or font input.
#include <QApplication>
#include <QStandardItemModel>
#include <QTimer>
#include <QTreeView>
#include <array>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <memory>
#include <unistd.h>
#include <vector>

class Model : public QAbstractItemModel {
public:
    enum Kind { Lazy, Deep, Wide, Invalid } kind;
    unsigned fetches = 0;
    explicit Model(Kind value) : kind(value) {}
    QModelIndex index(int row, int column, const QModelIndex &parent = {}) const override {
        if (kind == Invalid || column != 0 || row < 0 || row >= rowCount(parent)) return {};
        return createIndex(row, column, parent.isValid() ? parent.internalId()+1 : 1);
    }
    QModelIndex parent(const QModelIndex &index) const override {
        return kind == Deep && index.internalId() > 1 ? createIndex(0, 0, index.internalId()-1) : QModelIndex();
    }
    int rowCount(const QModelIndex &parent = {}) const override {
        if (kind == Lazy) return 0;
        if (kind == Deep) return parent.internalId() < 200 ? 1 : 0;
        return parent.isValid() ? 0 : (kind == Wide ? 10001 : 1);
    }
    int columnCount(const QModelIndex & = {}) const override { return 1; }
    QVariant data(const QModelIndex &, int = Qt::DisplayRole) const override { return {}; }
    bool canFetchMore(const QModelIndex &parent) const override { return kind == Lazy && !parent.isValid(); }
    void fetchMore(const QModelIndex &) override { ++fetches; }
};

int main(int argc, char **argv) {
    QApplication app(argc, argv);
    QStandardItemModel nested, empty;
    Model lazy(Model::Lazy), deep(Model::Deep), wide(Model::Wide), invalid(Model::Invalid);
    QAbstractItemModel *models[] = {&nested, &empty, &lazy, &deep, &wide, &invalid};
    const char *names[] = {"nested", "empty", "lazy", "deep", "wide", "invalid"};
    std::array<QTreeView, 6> views;
    for (int i = 0; i < 6; ++i) {
        views[i].setObjectName(QString::fromLatin1(names[i]));
        views[i].setModel(models[i]);
    }
    std::vector<std::unique_ptr<QTreeView>> extra;
    if (argc > 1 && std::strcmp(argv[1], "many") == 0)
        for (int i = 0; i < 65; ++i) extra.emplace_back(new QTreeView);
    QTimer::singleShot(1400, [&nested] {
        for (int i = 0; i < 2; ++i) {
            auto *root = new QStandardItem(QString::number(i));
            root->appendRow(new QStandardItem("original A"));
            root->appendRow(new QStandardItem("original B"));
            nested.appendRow(root);
        }
    });
    if (argc == 3 && std::strcmp(argv[1], "stop") == 0) {
        QTimer::singleShot(1500, [&] {
            int fd = open(argv[2], O_WRONLY|O_CREAT|O_EXCL, 0600);
            if (fd < 0) _exit(2);
            close(fd);
        });
    }
    QTimer::singleShot(3400, &app, &QApplication::quit);
    const int result = app.exec();
    // Qt's view can request lazy rows itself. Compare against an unobserved
    // run instead of incorrectly attributing every fetch to the observer.
    std::printf("fetches=%u\n", lazy.fetches);
    return result;
}
