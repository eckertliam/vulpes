#pragma once

#include "heap.hpp"
#include "instruction.hpp"
#include "vm/call_frame.hpp"

#include <stack>

namespace vulpes::vm {
    class Machine {
      public:
        void run();

      private:
        Heap heap_;
        std::vector<BaseObject*> globals_;
        std::stack<CallFrame> call_frames_;

        void execute_instruction(Instruction instruction);

        template <typename T, typename... Args> T* allocate(Args&&... args) {
            return heap_.allocate<T>(std::forward<Args>(args)...);
        }

        /* Garbage collection */
        void gc();

        /**
         * Returns all objects that are reachable from the roots.
         * Including global variables, functions, etc.
         */
        std::vector<BaseObject*> getRoots();

        /* Add a global and return the index */
        uint32_t addGlobal(BaseObject* global);

        /* Get a global by index */
        BaseObject* getGlobal(uint32_t index);
    };
} // namespace vulpes::vm