#pragma once

#include "object.hpp"
namespace vulpes::vm {

    struct alignas(std::max_align_t) ObjectHeader {
        uint32_t size;
        ObjectType type;
    };

    class Arena {
      private:
        char* base_;    // start of buffer
        char* current_; // current pos in buffer
        char* end_;     // end of buffer cap + base

        static constexpr size_t align_up(size_t size, size_t align) {
            return (size + (align - 1)) & ~(align - 1);
        }

      public:
        Arena(size_t cap) : base_(new char[cap]), current_(base_), end_(base_ + cap) {}

        ~Arena() { delete[] base_; }

        void* alloc_bytes(size_t size, size_t align = alignof(std::max_align_t)) {
            char* aligned =
                reinterpret_cast<char*>(align_up(reinterpret_cast<uintptr_t>(current_), align));
            if (aligned + size > end_) {
                // out of memory
                return nullptr;
            }

            current_ = aligned + size;

            return aligned;
        }

        template <class T, class... Args> T* make(Args&&... args) {
            // compute layout
            constexpr size_t HSIZE = sizeof(ObjectHeader);
            constexpr size_t OSIZE = sizeof(T);
            const size_t TOTAL = HSIZE + OSIZE;

            // allocate raw storage
            void* raw = alloc_bytes(TOTAL, alignof(std::max_align_t));
            if (!raw) throw std::bad_alloc();

            // initialize header
            auto* header = new (raw) ObjectHeader{
                static_cast<uint32_t>(TOTAL), ObjectType::String /* will be overwritten below */
            };

            // placement construct the actual object
            char* obj_mem = reinterpret_cast<char*>(raw) + HSIZE;
            T* obj = new (obj_mem) T(std::forward<Args>(args)...);

            // copy the runtime type tag from the object now that it exists
            header->type = obj->type;

            return obj;
        }

        void free_all() { current_ = base_; }

        // copy the live objects to a new arena
        Arena copy_live();
    };

} // namespace vulpes::vm