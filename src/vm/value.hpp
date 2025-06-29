#pragma once

#include <cstdint>
#include <variant>

namespace vulpes::vm {

    /**
     * @brief The type of a value.
     * @note The order of the enum is important and must match the order of the variant
     */
    enum class ValueType : uint8_t {
        Int = 0,
        Float = 1,
        Char = 2,
        Bool = 3,
        Null = 4,
        Object = 5,
    };

    class Object;

    /**
     * @brief A value in the VM.
     * @note It is important that the order of the variant matches the order of the ValueType
     */
    using ValueData = std::variant<int64_t, double, char, bool, std::nullptr_t, Object*>;

    class Value {
      public:
        Value(ValueData data) : data(data) {}

        const ValueData& raw() const { return data; }

        ValueType type_of() const;

        bool is_int() const { return std::holds_alternative<int64_t>(data); }
        bool is_float() const { return std::holds_alternative<double>(data); }
        bool is_char() const { return std::holds_alternative<char>(data); }
        bool is_bool() const { return std::holds_alternative<bool>(data); }
        bool is_null() const { return std::holds_alternative<std::nullptr_t>(data); }
        bool is_object() const { return std::holds_alternative<Object*>(data); }

        int64_t as_int() const { return std::get<int64_t>(data); }
        double as_float() const { return std::get<double>(data); }
        char as_char() const { return std::get<char>(data); }
        bool as_bool() const { return std::get<bool>(data); }
        std::nullptr_t as_null() const { return std::get<std::nullptr_t>(data); }
        Object* as_object() const { return std::get<Object*>(data); }

      private:
        ValueData data;
    };

    inline bool operator==(const Value& lhs, const Value& rhs) {
        return lhs.type_of() == rhs.type_of() && lhs.raw() == rhs.raw();
    }

    const Value NULL_VALUE = Value(nullptr);
    const Value TRUE_VALUE = Value(true);
    const Value FALSE_VALUE = Value(false);
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