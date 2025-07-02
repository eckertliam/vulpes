#pragma once

#include "value.hpp"

#include <string_view>
#include <unordered_map>
#include <vector>

namespace vulpes::vm {
    enum class ObjectType : uint8_t { String, List, Tuple, Table };

    class Object {
      public:
        bool is_marked = false;
        ObjectType type;
        virtual ~Object() = default;
    };

    class String : public Object {
      private:
        std::string data_;

      public:
        String(std::string data) : data_(data) { type = ObjectType::String; }

        std::string_view str() const { return data_; }

        Value get(Value index) const;

        Value length() const { return Value(static_cast<int64_t>(data_.size())); }

        String concat(const String& other) const;

        String operator+(Value other) const;
    };

    class List : public Object {
      private:
        std::vector<Value> data_;

      public:
        List() { type = ObjectType::List; }

        List(const std::vector<Value>& data) : data_(data) { type = ObjectType::List; }

        Value length() const { return Value(static_cast<int64_t>(data_.size())); }

        Value get(Value index) const;

        void push(const Value& value);

        Value pop();

        void clear() { data_.clear(); }

        void insert(size_t index, const Value& value);

        void remove(size_t index);

        void set(size_t index, const Value& value);

        Value contains(const Value& value) const;

        List concat(const List& other) const;

        List operator+(Value other) const;
    };

    class Tuple : public Object {
      private:
        std::vector<Value> data_;

      public:
        Tuple(std::vector<Value> data) : data_(data) { type = ObjectType::Tuple; }

        Value length() const { return Value(static_cast<int64_t>(data_.size())); }

        Value get(Value index) const;

        void set(Value index, const Value& value);
    };

    class Table : public Object {
      private:
        std::unordered_map<Value, Value> data_;

      public:
        Table() { type = ObjectType::Table; }

        Table(const std::unordered_map<Value, Value>& data) : data_(data) {
            type = ObjectType::Table;
        }

        Table(const std::vector<std::pair<Value, Value>>& data) {
            for (const auto& [key, value] : data) {
                data_.insert({key, value});
            }
            type = ObjectType::Table;
        }

        size_t size() const { return data_.size(); }

        Value get(const Value& key) const;

        void set(const Value& key, const Value& value);

        void remove(const Value& key);

        void clear() { data_.clear(); }

        Value contains(const Value& key) const;
    };
} // namespace vulpes::vm