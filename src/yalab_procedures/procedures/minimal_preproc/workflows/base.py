import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces.utility import Function, IdentityInterface
from yalab_procedures.interfaces.data_grabber.basic_requirements import (
    CollectRequiredInputs,
)
from bids.layout import BIDSLayout


def collect_required_inputs(subject_data: dict) -> tuple:
    """
    Collect required inputs for the minimal preprocessing workflow.
    """
    from bids.layout import parse_file_entities

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
                    v for v in value if parse_file_entities(v)["ceagent"] == "corrected"
                ]
                if len(value) > 1:
                    raise NotImplementedError(
                        f"Multiple {key} files are not supported."
                    )
                value = value[0]
            else:
                value = value[0]
            result[key] = value
    return [result.get(key) for key in ["dwi", "fmap", "t1w", "t2w"]]


def init_minimal_preproc_wf(
    name: str,
    subject_data: dict,
) -> pe.Workflow:
    """
    Create a minimal preprocessing workflow.
    """

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(  # noqa
        IdentityInterface(
            fields=[
                "bids_directory",
                "output_directory",
                "work_directory",
                "subject_id",
                "session_id",
                "do_smriprep",
                "subject_data",
            ]
        ),
        name="inputnode",
    )

    # BIDS
    # inputnode.inputs.layout = layout
    inputnode.inputs.subject_data = subject_data

    # Collect required inputs
    collect_inputs = pe.Node(
        CollectRequiredInputs(),
        name="collect_inputs",
    )

    wf.connect(
        [
            (inputnode, collect_inputs, [("subject_data", "subject_data")]),
        ]
    )

    return wf
