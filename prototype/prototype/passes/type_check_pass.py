from .base_pass import Pass
from .type_infer_pass import TypeInferencePass


# TODO: implement TypeCheckingPass
# This pass checks that all types are valid
class TypeCheckingPass(Pass):
    def __init__(self, previous_pass: TypeInferencePass):
        super().__init__(previous_pass=previous_pass)

    def run(self) -> None:
        # TODO: implement
        raise NotImplementedError("TypeCheckingPass not implemented")
