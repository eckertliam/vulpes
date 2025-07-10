#pragma once

#include "object/function.hpp"

#include <cstddef>

namespace vulpes::vm {
    using Function = object::Function;

    struct CallFrame {
        Function* function;
        size_t ip;
        size_t sp;

        CallFrame(Function* function, size_t ip, size_t sp) : function(function), ip(ip), sp(sp) {}
    };
} // namespace vulpes::vm