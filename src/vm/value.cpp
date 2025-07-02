#include "value.hpp"

#include "object.hpp"

#include <string>

namespace vulpes::vm {
    ValueType Value::type_of() const {
        return static_cast<ValueType>(data.index());
    }

    std::string Value::to_string() const {
        switch (type_of()) {
        case ValueType::Int:
            return std::to_string(as_int());
        case ValueType::Float:
            return std::to_string(as_float());
        case ValueType::Char:
            return std::to_string(as_char());
        case ValueType::Bool:
            return as_bool() ? "true" : "false";
        case ValueType::Null:
            return "null";
        case ValueType::Object: {
            // TODO: Implement to_string for objects
            Object* obj = as_object();
            switch (obj->type) {
            case ObjectType::String:
                return std::string(static_cast<String*>(obj)->str());
            case ObjectType::List:
                return "<List>";
            case ObjectType::Tuple:
                return "<Tuple>";
            case ObjectType::Table:
                return "<Table>";
            }
        }
        }
    }
} // namespace vulpes::vm