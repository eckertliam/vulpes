#pragma once

#include "object/base.hpp"

#include <algorithm>

namespace vulpes::vm {
using BaseObject = vulpes::vm::object::BaseObject;

class Heap {
 private:
  std::vector<std::unique_ptr<BaseObject>> objects_;

 public:
  Heap() : objects_() {}

  ~Heap() = default;

  template <typename T, typename... Args>
  T* allocate(Args&&... args) {
    auto object = std::make_unique<T>(std::forward<Args>(args)...);
    T* raw_ptr = object.get();
    objects_.push_back(std::move(object));
    return raw_ptr;
  }

  /* Mark objects from roots */
  void markFromRoots(const std::vector<BaseObject*>& roots);

  /* Sweep unmarked objects, then unmark the remnants*/
  void sweep();
};
}  // namespace vulpes::vm