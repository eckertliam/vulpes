#include "heap.hpp"

namespace vulpes::vm {
    static void markObject(BaseObject* obj) {
        if (!obj->isMarked()) {
            obj->mark();
            obj->trace(markObject);
        }
    }

    void Heap::markFromRoots(const std::vector<BaseObject*>& roots) {
        for (auto* root : roots) markObject(root);
    }

    void Heap::sweep() {
        objects_.erase(std::remove_if(objects_.begin(), objects_.end(),
                                      [](const std::unique_ptr<BaseObject>& obj) {
                                          return !obj->isMarked();
                                      }),
                       objects_.end());

        for (auto& obj : objects_) obj->unmark();
    }
} // namespace vulpes::vm