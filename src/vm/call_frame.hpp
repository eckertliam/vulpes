#pragma once

#include "function.hpp"

namespace vulpes::vm {
    struct CallFrame {
        Function* function;
        size_t ip;
        size_t sp;

        CallFrame(Function* function, size_t ip, size_t sp) : function(function), ip(ip), sp(sp) {}
    };
} // namespace vulpes::vm