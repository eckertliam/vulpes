#include "value.hpp"

#include <cstdint>

namespace vulpes::vm {
    ValueType Value::type_of() const {
        return static_cast<ValueType>(data.index());
    }
} // namespace vulpes::vm