from nipype.interfaces.base import (
    BaseInterface,
    BaseInterfaceInputSpec,
    TraitedSpec,
    traits,
)


class CollectRequiredInputsInputSpec(BaseInterfaceInputSpec):
    subject_data = traits.Dict(
        mandatory=True,
        desc="Subject data dictionary",
    )


class CollectRequiredInputsOutputSpec(TraitedSpec):
    dwi = traits.File(
        desc="Diffusion-weighted image file",
    )
    fmap = traits.File(
        desc="Fieldmap file",
    )
    t1w = traits.File(
        desc="T1-weighted image file",
    )
    t2w = traits.File(
        desc="T2-weighted image file",
    )


class CollectRequiredInputs(BaseInterface):
    input_spec = CollectRequiredInputsInputSpec
    output_spec = CollectRequiredInputsOutputSpec

    def _run_interface(self, runtime):
        from bids.layout import parse_file_entities

        subject_data = self.inputs.subject_data
        result = {}
        for key, direction in zip(["dwi", "fmap"], ["AP", "PA"]):
            value = subject_data.get(key)
            # if value is an empty list, raise an error
            if not value:
                raise ValueError(f"Missing {key} in subject data.")
            # if value is a list with more than one element, raise an error
            if len(value) > 1:
                raise NotImplementedError(f"Multiple {key} files are not supported.")
            value = value[0]
            entities = parse_file_entities(value)
            if entities["direction"] == direction:
                result[key] = value
        for key, required in zip(["t1w", "t2w"], [True, False]):
            value = subject_data.get(key)
            if required and not value:
                raise ValueError(f"Missing {key} in subject data.")
            if value:
                if len(value) > 1:
                    # choose the "ce" : "corrected" file
                    value = [
                        v
                        for v in value
                        if parse_file_entities(v)["ceagent"] == "corrected"
                    ]
                    if len(value) > 1:
                        raise NotImplementedError(
                            f"Multiple {key} files are not supported."
                        )
                    value = value[0]
                else:
                    value = value[0]
                result[key] = value
        self._results = {
            "dwi": result.get("dwi"),
            "fmap": result.get("fmap"),
            "t1w": result.get("t1w"),
            "t2w": result.get("t2w"),
        }
        return runtime

    def _list_outputs(self):
        return self._results
