#pragma once
#include <stdexcept>

namespace vulpes::vm {
class VMError : public std::runtime_error {
 public:
  VMError(const std::string& msg) : runtime_error(msg) {}
};

}  // namespace vulpes::vm
