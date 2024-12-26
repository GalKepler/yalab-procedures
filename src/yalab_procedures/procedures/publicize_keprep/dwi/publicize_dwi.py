import os
from pathlib import Path

import numpy as np
from neuromaps import datasets
from nipype.interfaces.mrtrix3 import MRConvert, MRTransform, TransformFSLConvert
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.pipeline import Node
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.bids import DerivativesDataSink as _DDSink

from yalab_procedures.procedures.publicize_keprep.dwi.utils import FullMRTransform

_DDSink.out_path_base = ""
STANDARD_REFERENCE = datasets.fetch_atlas(atlas="mni", density="1mm").get(
    "2009cAsym_T1w"
)


def rotate_bvecs(bvec_file, aff, warp=None):
    """
    Adjusts the bvecs using the affine transformations DWI -> T1w -> MNI.
    Parameters:
        bvec_file: Path to the original .bvec file
        aff1: Affine transformation matrix (DWI -> T1w)
        aff2: Affine transformation matrix (T1w -> MNI)
    Returns:
        rotated_bvec_file: Path to the adjusted .bvec file
    """
    # Load the original bvec
    bvecs = np.loadtxt(bvec_file)

    # Load the affine transformations
    aff_matrix = np.loadtxt(aff)[:3, :3]  # Extract rotation matrix from aff1

    # Apply rotation to each gradient vector
    rotated_bvecs = np.dot(aff_matrix, bvecs)
    rotated_bvecs = rotated_bvecs / np.linalg.norm(rotated_bvecs, axis=0)  # Normalize

    # Save the rotated bvec
    rotated_bvec_file = os.path.abspath("rotated.bvec")
    np.savetxt(rotated_bvec_file, rotated_bvecs, fmt="%.6f")
    return rotated_bvec_file


def collect_inputs_multiple_sessions(
    input_directory: str,
    participant_label: str,
    session_id: str = None,
    is_preproc: bool = True,
    is_affine: bool = False,
):
    """
    Collect inputs required for anatomical standardization.

    Parameters
    ----------
    input_directory : Path
        Keprep directory
    participant_label : str
        Participant label
    """
    from pathlib import Path

    from yalab_procedures.procedures.publicize_keprep.utils import get_file

    regex_suffix = "_desc-preproc_dwi" if is_preproc else "_dwi"
    regex_suffix = "_from-T1w_to-dwi_mode-image_xfm" if is_affine else regex_suffix
    input_directory = Path(input_directory)
    subject_dir = input_directory / f"sub-{participant_label}"
    if session_id is not None:
        subject_dir = subject_dir / f"ses-{session_id}"
    if not subject_dir.exists():
        raise FileNotFoundError(f"Directory {subject_dir} does not exist.")
    anat_dir = subject_dir / "anat"
    if not anat_dir.exists():
        raise FileNotFoundError(f"Directory {anat_dir} does not exist.")
    result = get_file(
        anat_dir,
        participant_label=participant_label,
        regex=f"ce-corrected*{regex_suffix}",
        extension=".txt" if is_affine else ".nii.gz",
        get_associated_files=False if is_affine else True,
        is_dwi=True,
    )
    if is_affine:
        return result
    dwi_nifti, dwi_json, bval, bvec = result
    return dwi_nifti, dwi_json, bval, bvec


def init_dwi_wf(
    keprep_directory: Path, participant_label: str, name: str = "publicize_dwi_wf"
) -> Workflow:
    """
    Initialize the publicize workflow
    """
    sessions = [
        x.name.split("-")[-1]
        for x in keprep_directory.glob(f"sub-{participant_label}/ses-*")
    ]
    workflow = Workflow(name=name)
    input_node = Node(
        IdentityInterface(
            fields=[
                "input_directory",
                "participant_label",
                "t1w_nii",
                "t1w_to_mni_aff",
                "nonlinear_warp",
            ]
        ),
        name="input_node",
    )
    for session in sessions:
        session_workflow = init_session_workflow(session)
        workflow.connect(
            [
                (
                    input_node,
                    session_workflow,
                    [
                        ("input_directory", "input_node.keprep_directory"),
                        ("participant_label", "input_node.participant_label"),
                        ("t1w_nii", "input_node.t1w_nii"),
                        ("t1w_to_mni_aff", "input_node.t1w_to_mni_aff"),
                        ("nonlinear_warp", "input_node.nonlinear_warp"),
                    ],
                )
            ]
        )
    return workflow


def init_session_workflow(session_id: str) -> Workflow:
    """
    Initialize the session workflow
    """
    workflow = Workflow(name=f"session_{session_id}_wf")
    input_node = Node(
        IdentityInterface(
            fields=[
                "keprep_directory",
                "participant_label",
                "session_id",
                "t1w_nii",
                "t1w_to_mni_aff",
                "nonlinear_warp",
            ]
        ),
        name="input_node",
    )
    input_node.inputs.session_id = session_id
    # Get session T1w image
    collect_inputs = Node(
        Function(
            input_names=[
                "input_directory",
                "participant_label",
                "session_id",
                "is_preproc",
                "is_affine",
            ],
            output_names=["dwi_nii", "dwi_json", "bval", "bvec"],
            function=collect_inputs_multiple_sessions,
        ),
        name="collect_inputs",
    )
    collect_inputs.inputs.is_preproc = True
    collect_inputs.inputs.is_affine = False

    collect_dwi_to_t1w_aff = Node(
        Function(
            input_names=[
                "input_directory",
                "participant_label",
                "session_id",
                "is_preproc",
                "is_affine",
            ],
            output_names=["dwi_to_t1w_aff"],
            function=collect_inputs_multiple_sessions,
        ),
        name="collect_dwi_to_t1w_aff",
    )
    collect_dwi_to_t1w_aff.inputs.is_preproc = False
    collect_dwi_to_t1w_aff.inputs.is_affine = True

    workflow.connect(
        [
            (
                input_node,
                collect_inputs,
                [
                    ("keprep_directory", "input_directory"),
                    ("participant_label", "participant_label"),
                    ("session_id", "session_id"),
                ],
            ),
            (
                input_node,
                collect_dwi_to_t1w_aff,
                [
                    ("keprep_directory", "input_directory"),
                    ("participant_label", "participant_label"),
                    ("session_id", "session_id"),
                ],
            ),
        ]
    )

    # convert dwi to mif format
    convert_dwi = Node(MRConvert(), name="convert_dwi")
    workflow.connect(
        [
            (
                collect_inputs,
                convert_dwi,
                [
                    ("dwi_nii", "in_file"),
                    ("dwi_json", "json_import"),
                    ("bval", "in_bval"),
                    ("bvec", "in_bvec"),
                ],
            )
        ]
    )
    # convert FLIRT affine to MRtrix format
    convert_affine = Node(TransformFSLConvert(flirt_import=True), name="convert_affine")
    workflow.connect(
        [
            (
                collect_dwi_to_t1w_aff,
                convert_affine,
                [
                    ("dwi_to_t1w_aff", "in_transform"),
                ],
            ),
            (
                convert_dwi,
                convert_affine,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (
                input_node,
                convert_affine,
                [
                    ("t1w_nii", "reference"),
                ],
            ),
        ]
    )
    # apply transforms to image
    apply_transform_to_t1w = Node(MRTransform(), name="apply_transform_to_t1w")
    workflow.connect(
        [
            (
                convert_affine,
                apply_transform_to_t1w,
                [
                    ("dwi_to_t1w_aff", "linear_transform"),
                ],
            ),
            (
                convert_dwi,
                apply_transform_to_t1w,
                [
                    ("out_file", "in_files"),
                ],
            ),
        ]
    )
    # transform mif to nii
    dwi_in_t1w_space = Node(
        MRConvert(
            out_file="dwi.nii.gz",
            out_bvec="dwi.bvec",
            out_bval="dwi.bval",
            json_export="dwi.json",
        ),
        name="dwi_in_t1w_space",
    )
    workflow.connect(
        [
            (
                apply_transform_to_t1w,
                dwi_in_t1w_space,
                [
                    ("out_file", "in_file"),
                ],
            )
        ]
    )
    # dsink
    for key, extension in zip(
        ["out_file", "out_bvec", "out_bval", "json_export"],
        ["nii.gz", "bvec", "bval", "json"],
    ):
        dsink = Node(_DDSink(space="T1w", extension=extension), name=f"dsink_{key}")
        workflow.connect(
            [
                (
                    input_node,
                    dsink,
                    [
                        ("input_directory", "base_directory"),
                    ],
                ),
                (
                    collect_inputs,
                    dsink,
                    [
                        ("dwi_nii", "source_file"),
                    ],
                ),
                (
                    dwi_in_t1w_space,
                    dsink,
                    [
                        (key, "in_file"),
                    ],
                ),
            ]
        )
    # apply transforms to MNI
    apply_transform_to_mni = Node(FullMRTransform(), name="apply_transform_to_mni")
    apply_transform_to_mni.inputs.template_image = STANDARD_REFERENCE
    workflow.connect(
        [
            (
                input_node,
                apply_transform_to_mni,
                [("t1w_to_mni_aff", "linear_transform"), ("nonlinear_warp", "warp")],
            ),
            (
                convert_dwi,
                apply_transform_to_mni,
                [
                    ("out_file", "in_file"),
                ],
            ),
        ]
    )
    # transform mif to nii
    dwi_in_mni_space = Node(
        MRConvert(
            out_file="dwi_in_mni.nii.gz",
            out_bvec="dwi_in_mni.bvec",
            out_bval="dwi_in_mni.bval",
            json_export="dwi_in_mni.json",
        ),
        name="dwi_in_mni_space",
    )
    workflow.connect(
        [
            (
                apply_transform_to_mni,
                dwi_in_mni_space,
                [
                    ("out_file", "in_file"),
                ],
            )
        ]
    )
    # dsink
    for key, extension in zip(
        ["out_file", "out_bvec", "out_bval", "json_export"],
        ["nii.gz", "bvec", "bval", "json"],
    ):
        dsink = Node(
            _DDSink(space="MNI152NLin2009cAsym", extension=extension),
            name=f"dsink_{key}",
        )
        workflow.connect(
            [
                (
                    input_node,
                    dsink,
                    [
                        ("input_directory", "base_directory"),
                    ],
                ),
                (
                    collect_inputs,
                    dsink,
                    [
                        ("dwi_nii", "source_file"),
                    ],
                ),
                (
                    dwi_in_mni_space,
                    dsink,
                    [
                        (key, "in_file"),
                    ],
                ),
            ]
        )
