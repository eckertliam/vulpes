#pragma once

#include <cstdint>

namespace vulpes::vm {
    enum class ValueType : uint8_t {
        Int,
        Char,
        Float,
        Null,
        Bool,
    };

    struct Value {
        ValueType type;
        union {
            int64_t int_value;
            char char_value;
            float float_value;
            bool bool_value;
        } as;
    };
} // namespace vulpes::vm