#include "value.hpp"

#include <cstdint>

namespace vulpes::vm {
    ValueType Value::type_of() const {
        return static_cast<ValueType>(data.index());
    }
} // namespace vulpes::vm

namespace std {
    template <> struct hash<vulpes::vm::Value> {
        size_t operator()(const vulpes::vm::Value& value) const {
            static const size_t type_hashes[] = {
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Int)),
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Float)),
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Char)),
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Bool)),
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Null)),
                std::hash<uint8_t>{}(static_cast<uint8_t>(vulpes::vm::ValueType::Object)),
            };

            const auto type = value.type_of();
            const auto& data = value.raw();
            const size_t type_hash = type_hashes[static_cast<size_t>(type)];
            const size_t data_hash = std::visit(
                [](const auto& val) -> size_t {
                    if constexpr (std::is_same_v<std::decay_t<decltype(val)>, std::nullptr_t>) {
                        // nullptr is a special case, we use a constant hash
                        return 0x9e3779b9;
                    } else {
                        // For other types, we use the hash of the value
                        return std::hash<std::decay_t<decltype(val)>>{}(val);
                    }
                },
                data);

            return type_hash ^ (data_hash + 0x9e3779b9 + (type_hash << 6) + (type_hash >> 2));
        }
    };
} // namespace std