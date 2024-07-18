import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

from yalab_procedures.interfaces.data_grabber.basic_requirements import (
    CollectRequiredInputs,
)
from yalab_procedures.procedures.smriprep.smriprep import SmriprepProcedure

# def collect_required_inputs(subject_data: dict) -> tuple:
#     """
#     Collect required inputs for the minimal preprocessing workflow.
#     """
#     from bids.layout import parse_file_entities

#     result = {}
#     for key, direction in zip(["dwi", "fmap"], ["AP", "PA"]):
#         value = subject_data.get(key)
#         # if value is an empty list, raise an error
#         if not value:
#             raise ValueError(f"Missing {key} in subject data.")
#         # if value is a list with more than one element, raise an error
#         if len(value) > 1:
#             raise NotImplementedError(f"Multiple {key} files are not supported.")
#         value = value[0]
#         entities = parse_file_entities(value)
#         if entities["direction"] == direction:
#             result[key] = value
#     for key, required in zip(["t1w", "t2w"], [True, False]):
#         value = subject_data.get(key)
#         if required and not value:
#             raise ValueError(f"Missing {key} in subject data.")
#         if value:
#             if len(value) > 1:
#                 # choose the "ce" : "corrected" file
#                 value = [
#                     v for v in value if parse_file_entities(v)["ceagent"] == "corrected"
#                 ]
#                 if len(value) > 1:
#                     raise NotImplementedError(
#                         f"Multiple {key} files are not supported."
#                     )
#                 value = value[0]
#             else:
#                 value = value[0]
#             result[key] = value
#     return [result.get(key) for key in ["dwi", "fmap", "t1w", "t2w"]]


def rename_smriprep_output(
    output_directory: str, subject_id: str, new_name: str = "dmriprep"
) -> str:
    """
    Rename the output directory of smriprep.
    """
    import os
    from pathlib import Path

    smriprep_dir = Path(output_directory) / "smriprep" / f"sub-{subject_id}"
    new_output_directory = str(smriprep_dir.parent / new_name / f"sub-{subject_id}")
    os.rename(str(smriprep_dir), new_output_directory)
    return new_output_directory


def init_minimal_preproc_wf(
    subject_id: str,
    subject_data: dict,
    name: str = "minimal_preproc_wf",
) -> pe.Workflow:
    """
    Create a minimal preprocessing workflow.
    """

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(  # noqa
        niu.IdentityInterface(
            fields=[
                "bids_directory",
                "output_directory",
                "work_directory",
                "subject_id",
                "session_id",
                "subject_data",
                "bids_filters",
                "fs_license_file",
                "force",
            ]
        ),
        name="inputnode",
    )

    # BIDS
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

    # Smriprep
    smriprep = pe.Node(SmriprepProcedure(), name="smriprep")

    # rename smriprep output
    rename_output = pe.Node(
        niu.Function(
            input_names=["output_directory"],
            output_names=["new_output_directory"],
            function=rename_smriprep_output,
        ),
        name="rename_output",
    )

    wf.connect(
        [
            (
                inputnode,
                smriprep,
                [
                    ("bids_directory", "input_directory"),
                    ("output_directory", "output_directory"),
                    ("work_directory", "work_directory"),
                    ("subject_id", "participant_label"),
                    ("bids_filters", "bids_filters"),
                    ("fs_license_file", "fs_license_file"),
                    ("force", "force"),
                ],
            ),
            (smriprep, rename_output, [("output_directory", "output_directory")]),
        ]
    )

    return wf
