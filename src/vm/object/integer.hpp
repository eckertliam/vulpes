#pragma once

#include "base.hpp"

namespace vulpes::vm::object {
    struct Integer {
        ObjectHeader header;
        int64_t value;

        Integer(int64_t value);
        ~Integer() { header.dec_ref_count(); }
    };
} // namespace vulpes::vm::object