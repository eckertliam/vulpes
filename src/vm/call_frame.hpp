#pragma once

#include "object/function.hpp"

namespace vulpes::vm {
using Function = object::Function;

struct CallFrame {
  Function* function;
  size_t ip;
  size_t sp;

  CallFrame(Function* function, size_t sp)
      : function(function), ip(0), sp(sp) {}
};
}  // namespace vulpes::vm