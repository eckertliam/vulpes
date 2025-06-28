#include "arena.hpp"

namespace vulpes::vm {

    Arena Arena::copy_live() {
        Arena new_arena(end_ - base_);
        char* cursor = base_;

        while (cursor < current_) {
            ObjectHeader* header = reinterpret_cast<ObjectHeader*>(cursor);

            switch (header->type) {
            case ObjectType::String: {
                auto* old_str = reinterpret_cast<String*>(cursor + sizeof(ObjectHeader));
                auto* new_str = new_arena.make<String>(std::move(*old_str));
                break;
            }
            case ObjectType::List: {
                auto* old_list = reinterpret_cast<List*>(cursor + sizeof(ObjectHeader));
                auto* new_list = new_arena.make<List>(std::move(*old_list));
                break;
            }
            case ObjectType::Tuple: {
                auto* old_tuple = reinterpret_cast<Tuple*>(cursor + sizeof(ObjectHeader));
                auto* new_tuple = new_arena.make<Tuple>(std::move(*old_tuple));
                break;
            }
            case ObjectType::Table: {
                auto* old_table = reinterpret_cast<Table*>(cursor + sizeof(ObjectHeader));
                auto* new_table = new_arena.make<Table>(std::move(*old_table));
                break;
            }
            }

            cursor += header->size;
        }

        return new_arena;
    }

} // namespace vulpes::vm