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