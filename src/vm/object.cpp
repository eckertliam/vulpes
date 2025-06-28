#include "object.hpp"

#include "value.hpp"

#include <cstdint>

namespace vulpes::vm {
    Value String::get(Value index) const {
        if (index.type_of() != ValueType::Int) {
            throw std::runtime_error("Index must be an integer");
        }

        const int64_t idx = std::get<int64_t>(index.raw());
        if (idx < 0 || idx >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        return Value(data_[idx]);
    }

    String String::concat(const String& other) const {
        String result(data_ + other.data_);
        return result;
    }

    String String::operator+(Value other) const {
        switch (other.type_of()) {
        case ValueType::Char:
            return String(data_ + std::get<char>(other.raw()));
        case ValueType::Int:
            return String(data_ + std::to_string(std::get<int64_t>(other.raw())));
        case ValueType::Float:
            return String(data_ + std::to_string(std::get<double>(other.raw())));
        case ValueType::Bool:
            return String(data_ + std::to_string(std::get<bool>(other.raw())));
        case ValueType::Null:
            throw std::runtime_error("Cannot concatenate string with null value");
        case ValueType::Object: {
            Object* obj = std::get<Object*>(other.raw());
            if (obj->type == ObjectType::String) {
                String* str = static_cast<String*>(obj);
                return concat(*str);
            } else {
                throw std::runtime_error("Cannot concatenate string with non-string object");
            }
        }
        default:
            throw std::runtime_error("Cannot concatenate string with unknown type");
        }
    }

    Value List::get(Value index) const {
        if (index.type_of() != ValueType::Int) {
            throw std::runtime_error("Index must be an integer");
        }

        const int64_t idx = std::get<int64_t>(index.raw());
        if (idx < 0 || idx >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }
    }

    void List::push(const Value& value) {
        data_.push_back(value);
    }

    Value List::pop() {
        if (data_.empty()) {
            throw std::runtime_error("List is empty");
        }

        const Value value = data_.back();
        data_.pop_back();
        return value;
    }

    void List::insert(size_t index, const Value& value) {
        if (index < 0 || index >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        data_.insert(data_.begin() + index, value);
    }

    void List::remove(size_t index) {
        if (index < 0 || index >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        data_.erase(data_.begin() + index);
    }

    void List::set(size_t index, const Value& value) {
        if (index < 0 || index >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        data_[index] = value;
    }

    Value List::contains(const Value& value) const {
        for (const auto& item : data_) {
            if (item == value) {
                return TRUE_VALUE;
            }
        }

        return FALSE_VALUE;
    }

    List List::concat(const List& other) const {
        List result;
        result.data_ = data_;
        result.data_.insert(result.data_.end(), other.data_.begin(), other.data_.end());
        return result;
    }

    List List::operator+(Value other) const {
        if (other.type_of() != ValueType::Object) {
            throw std::runtime_error("Cannot concatenate list with non-object value");
        }

        Object* obj = std::get<Object*>(other.raw());
        if (obj->type == ObjectType::List) {
            return concat(*static_cast<List*>(obj));
        } else {
            throw std::runtime_error("Cannot concatenate list with non-list object");
        }
    }

    Value Tuple::get(Value index) const {
        if (index.type_of() != ValueType::Int) {
            throw std::runtime_error("Index must be an integer");
        }

        const int64_t idx = std::get<int64_t>(index.raw());
        if (idx < 0 || idx >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        return data_[idx];
    }

    void Tuple::set(Value index, const Value& value) {
        if (index.type_of() != ValueType::Int) {
            throw std::runtime_error("Index must be an integer");
        }

        const int64_t idx = std::get<int64_t>(index.raw());
        if (idx < 0 || idx >= data_.size()) {
            throw std::runtime_error("Index out of bounds");
        }

        data_[idx] = value;
    }
} // namespace vulpes::vm