#include "function.hpp"

namespace vulpes::vm::object {
    void Function::trace(const std::function<void(BaseObject*)>& visit) {
        visit(this);
        for (auto* arg : args_) visit(arg);
        for (auto* constant : constants_) visit(constant);
        for (auto* local : locals_) visit(local);
    }
} // namespace vulpes::vm::object