#pragma once

#include <cstdint>

namespace vulpes::vm::object {
    struct TypeInfo;

    struct ObjectHeader {
        uint32_t ref_count;
        TypeInfo* type_info;

        ObjectHeader(TypeInfo* type_info) : ref_count(0), type_info(type_info) {}

        void inc_ref_count() { ref_count++; }

        void dec_ref_count() { ref_count--; }
    };

    enum class TypeId : uint16_t {
        Invalid = 0xFFFF,
        Integer = 0,
        Float = 1,
        Boolean = 2,
        Null = 3,
        String = 4,
        List = 5,
        Map = 6,
        Function = 7,
        Class = 8,
        Instance = 9,
    };

    inline const char* type_id_to_string(TypeId type_id) {
        switch (type_id) {
        case TypeId::Integer:
            return "Integer";
        case TypeId::Float:
            return "Float";
        case TypeId::Boolean:
            return "Boolean";
        case TypeId::Null:
            return "Null";
        case TypeId::String:
            return "String";
        case TypeId::List:
            return "List";
        case TypeId::Map:
            return "Map";
        case TypeId::Function:
            return "Function";
        case TypeId::Class:
            return "Class";
        case TypeId::Instance:
            return "Instance";
        case TypeId::Invalid:
            return "Invalid";
        default:
            return "Unknown";
        }
    }

    struct TypeInfo {
        const char* name;
        TypeId type_id;
        size_t size;
        size_t align;

        // Introspection
        void (*print)(ObjectHeader*);
        uint64_t (*hash)(ObjectHeader*);

        // Memory management
        void (*destroy)(ObjectHeader*);
        void (*copy)(ObjectHeader*, ObjectHeader*);
        void (*move)(ObjectHeader*, ObjectHeader*);

        // Comparison
        bool (*equals)(ObjectHeader*, ObjectHeader*);
    };

    // used for hash functions
    static inline uint64_t mix64(uint64_t x) {
        // Bit mixing hash (variant of MurmurHash3 finalizer)
        // Provides good distribution for integer values
        x ^= x >> 33;
        x *= 0xff51afd7ed558ccdULL;
        x ^= x >> 33;
        x *= 0xc4ceb9fe1a85ec53ULL;
        x ^= x >> 33;

        return x;
    }
} // namespace vulpes::vm::object