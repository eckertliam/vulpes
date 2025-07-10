#include "integer.hpp"

#include "vm/object/base.hpp"

#include <cstdio>

namespace vulpes::vm::object {
    static inline Integer* integer_from_header(ObjectHeader* header) {
        return reinterpret_cast<Integer*>(header);
    }

    static void integer_print(ObjectHeader* header) {
        // safe cast: obj points to header which is at offset 0
        Integer* integer = integer_from_header(header);
        printf("%lld", integer->value);
    }

    static uint64_t integer_hash(ObjectHeader* header) {
        Integer* integer = integer_from_header(header);
        uint64_t x = static_cast<uint64_t>(integer->value);

        return mix64(x);
    }

    static void integer_destroy(ObjectHeader* header) {
        Integer* integer = integer_from_header(header);
        delete integer;
    }

    static void integer_copy(ObjectHeader* src, ObjectHeader* dst) {
        Integer* src_integer = integer_from_header(src);
    }

    static void integer_move(ObjectHeader* src, ObjectHeader* dst) {
        Integer* src_integer = integer_from_header(src);
        Integer* dst_integer = integer_from_header(dst);
        dst_integer->value = src_integer->value;
    }

    static bool integer_equals(ObjectHeader* a, ObjectHeader* b) {
        Integer* a_integer = integer_from_header(a);
        Integer* b_integer = integer_from_header(b);
        return a_integer->value == b_integer->value;
    }

    static TypeInfo integer_type_info = {
        .name = "Integer",
        .type_id = TypeId::Integer,
        .size = sizeof(Integer),
        .align = alignof(Integer),
        .print = integer_print,
        .hash = integer_hash,
        .destroy = integer_destroy,
        .copy = integer_copy,
        .move = integer_move,
        .equals = integer_equals,
    };

    // Constructor implementation
    Integer::Integer(int64_t value) : header(&integer_type_info), value(value) {
        header.inc_ref_count();
    }
} // namespace vulpes::vm::object