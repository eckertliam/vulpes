#pragma once

#include <cstdint>

namespace vulpes::vm {
    class Arena {
      private:
        uint8_t* start;
        uint8_t* current;
        uint8_t* end;

        /* Find the next aligned address */
        static uintptr_t align_up(uintptr_t addr, size_t align) {
            return (addr + align - 1) & ~(align - 1);
        }

        void* raw_alloc(size_t size, size_t align) {
            // Find the next aligned address
            uintptr_t aligned_current = align_up(reinterpret_cast<uintptr_t>(current), align);
            uint8_t* aligned_ptr = reinterpret_cast<uint8_t*>(aligned_current);

            // Check if we have enough space
            if (aligned_ptr + size > end) {
                return nullptr;
            }

            current = aligned_ptr + size;
            return aligned_ptr;
        }

      public:
        Arena(size_t size) {
            start = new uint8_t[size];
            current = start;
            end = start + size;
        }

        ~Arena() { delete[] start; }

        template <typename T> T* allocate(size_t count = 1) {
            return static_cast<T*>(raw_alloc(sizeof(T) * count, alignof(T)));
        }
    };

} // namespace vulpes::vm