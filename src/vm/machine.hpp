#pragma once

#include "instruction.hpp"

namespace vulpes::vm {
    class Machine {
      public:
        void run();

      private:
        void execute_instruction(Instruction instruction);
    };
} // namespace vulpes::vm