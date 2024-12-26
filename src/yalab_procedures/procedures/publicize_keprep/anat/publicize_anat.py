from pathlib import Path

from neuromaps import datasets
from nipype.interfaces.ants import ApplyTransforms
from nipype.interfaces.fsl import FLIRT, FNIRT, ApplyWarp
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.pipeline import Node
from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.bids import DerivativesDataSink as _DDSink

_DDSink.out_path_base = ""
STANDARD_REFERENCE = datasets.fetch_atlas(atlas="mni", density="1mm").get(
    "2009cAsym_T1w"
)


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

    regex_suffix = "_desc-preproc_T1w" if is_preproc else "_T1w"
    regex_suffix = "_from-orig_to-T1w_mode-image_xfm" if is_affine else regex_suffix
    input_directory = Path(input_directory)
    subject_dir = input_directory / f"sub-{participant_label}"
    if session_id is not None:
        subject_dir = subject_dir / f"ses-{session_id}"
    if not subject_dir.exists():
        raise FileNotFoundError(f"Directory {subject_dir} does not exist.")
    anat_dir = subject_dir / "anat"
    if not anat_dir.exists():
        raise FileNotFoundError(f"Directory {anat_dir} does not exist.")
    try:
        result = get_file(
            anat_dir,
            participant_label=participant_label,
            regex=f"ce-corrected*{regex_suffix}",
            extension=".txt" if is_affine else ".nii.gz",
            get_associated_files=False if is_affine else True,
        )
    except FileNotFoundError:
        result = get_file(
            anat_dir,
            participant_label=participant_label,
            regex=f"ce-uncorrected*{regex_suffix}",
            extension=".txt" if is_affine else ".nii.gz",
            get_associated_files=False if is_affine else True,
        )
    if is_affine:
        return result
    t1w_nii, t1w_json = result
    return t1w_nii, t1w_json


def init_anat_wf(
    bids_directory: Path, participant_label: str, name: str = "publicize_anat_wf"
) -> Workflow:
    """
    Initialize the publicize workflow
    """
    sessions = [
        x.name.split("-")[-1]
        for x in bids_directory.glob(f"sub-{participant_label}/ses-*")
    ]
    workflow = Workflow(name=name)
    input_node = Node(
        IdentityInterface(
            fields=["input_directory", "bids_directory", "participant_label"]
        ),
        name="input_node",
    )
    collect_inputs = Node(
        Function(
            input_names=[
                "input_directory",
                "participant_label",
                "session_id",
                "is_preproc",
                "is_affine",
            ],
            output_names=["t1w_nii", "t1w_json"],
            function=collect_inputs_multiple_sessions,
        ),
        name="collect_inputs",
    )
    if len(sessions) > 1:
        collect_inputs.inputs.session_id = None
    else:
        collect_inputs.inputs.session_id = sessions[0]
    collect_inputs.inputs.is_preproc = True
    collect_inputs.inputs.is_affine = False
    # flirt and fnirt

    # flirt with 12 degrees of freedom and mutual information cost function
    flirt = Node(
        FLIRT(reference=STANDARD_REFERENCE, dof=12, cost="mutualinfo"), name="flirt"
    )
    fnirt = Node(
        FNIRT(
            ref_file=STANDARD_REFERENCE,
            field_file="field.nii.gz",
            fieldcoeff_file="fieldcoeff.nii.gz",
            jacobian_file="jacobian.nii.gz",
            modulatedref_file="modulatedref.nii.gz",
            out_intensitymap_file="intensitymap.nii.gz",
            warped_file="warped.nii.gz",
        ),
        name="fnirt",
    )
    workflow.connect(
        [
            (
                input_node,
                collect_inputs,
                [
                    ("input_directory", "input_directory"),
                    ("participant_label", "participant_label"),
                ],
            ),
            (collect_inputs, flirt, [("t1w_nii", "in_file")]),
            (flirt, fnirt, [("out_matrix_file", "affine_file")]),
            (collect_inputs, fnirt, [("t1w_nii", "in_file")]),
        ]
    )
    for session in sessions:
        session_wf = init_session_workflow(session, len(sessions) > 1)
        workflow.connect(
            [
                (
                    collect_inputs,
                    session_wf,
                    [("t1w_nii", "orig_to_t1w.reference_image")],
                ),
                (
                    flirt,
                    session_wf,
                    [
                        ("out_matrix_file", "input_node.affine_matrix"),
                    ],
                ),
                (
                    fnirt,
                    session_wf,
                    [
                        ("fieldcoeff_file", "input_node.nonlinear_warp"),
                    ],
                ),
                (
                    input_node,
                    session_wf,
                    [
                        ("input_directory", "input_node.keprep_directory"),
                        ("bids_directory", "input_node.bids_directory"),
                        ("participant_label", "input_node.participant_label"),
                    ],
                ),
            ]
        )
    return workflow


def init_session_workflow(session_id: str, multiple_sessions: bool) -> Workflow:
    """
    Initialize the session workflow
    """
    workflow = Workflow(name=f"session_{session_id}_wf")
    input_node = Node(
        IdentityInterface(
            fields=[
                "keprep_directory",
                "bids_directory",
                "participant_label",
                "session_id",
                "affine_matrix",
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
            output_names=["t1w_nii", "t1w_json"],
            function=collect_inputs_multiple_sessions,
        ),
        name="collect_inputs",
    )
    collect_inputs.inputs.is_preproc = False
    collect_inputs.inputs.is_affine = False

    workflow.connect(
        [
            (
                input_node,
                collect_inputs,
                [
                    ("bids_directory", "input_directory"),
                    ("participant_label", "participant_label"),
                    ("session_id", "session_id"),
                ],
            ),
        ]
    )

    dsink_session_t1w_orig = Node(
        _DDSink(space="T1w", extension=".nii.gz"),
        name="dsink_session_t1w_orig",
    )
    dsink_session_t1w_json_orig = Node(
        _DDSink(space="T1w", extension=".json"),
        name="dsink_session_t1w_json_orig",
    )
    # Apply warp to move the raw T1w from session to MNI space
    dsink_t1w_to_mni = Node(
        _DDSink(space="MNI152NLin2009cAsym", extension=".nii.gz"),
        name="dsink_t1w_to_mni",
    )
    dsink_t1w_to_mni_json = Node(
        _DDSink(space="MNI152NLin2009cAsym", extension=".json"),
        name="dsink_t1w_to_mni_json",
    )
    apply_warp = Node(ApplyWarp(ref_file=STANDARD_REFERENCE), name="apply_warp")

    if multiple_sessions:
        # get session-to-anatomical space affine - use get_file function
        collect_affine = Node(
            Function(
                input_names=[
                    "input_directory",
                    "participant_label",
                    "session_id",
                    "is_preproc",
                    "is_affine",
                ],
                output_names=["orig_to_t1w"],
                function=collect_inputs_multiple_sessions,
            ),
            name="collect_affine",
        )
        collect_affine.inputs.is_preproc = False
        collect_affine.inputs.is_affine = True
        workflow.connect(
            [
                (
                    input_node,
                    collect_affine,
                    [
                        ("keprep_directory", "input_directory"),
                        ("participant_label", "participant_label"),
                        ("session_id", "session_id"),
                    ],
                ),
            ]
        )
        # first, apply XFM to move the raw T1w from session to anatomical space
        orig_to_t1w = Node(ApplyTransforms(), name="orig_to_t1w")
        workflow.connect(
            [
                (
                    collect_inputs,
                    orig_to_t1w,
                    [("t1w_nii", "input_image")],
                ),
                (collect_affine, orig_to_t1w, [("orig_to_t1w", "transforms")]),
                (orig_to_t1w, dsink_session_t1w_orig, [("output_image", "in_file")]),
                (
                    input_node,
                    dsink_session_t1w_orig,
                    [("keprep_directory", "base_directory")],
                ),
                (collect_inputs, dsink_session_t1w_orig, [("t1w_nii", "source_file")]),
                (
                    collect_inputs,
                    dsink_session_t1w_json_orig,
                    [("t1w_json", "in_file")],
                ),
                (
                    input_node,
                    dsink_session_t1w_json_orig,
                    [("keprep_directory", "base_directory")],
                ),
                (
                    collect_inputs,
                    dsink_session_t1w_json_orig,
                    [("t1w_json", "source_file")],
                ),
                (orig_to_t1w, apply_warp, [("output_image", "in_file")]),
            ]
        )
    else:
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
                    collect_inputs,
                    dsink_session_t1w_orig,
                    [("t1w_nii", "in_file"), ("t1w_nii", "source_file")],
                ),
                (
                    collect_inputs,
                    dsink_session_t1w_json_orig,
                    [("t1w_json", "in_file"), ("t1w_json", "source_file")],
                ),
                (
                    input_node,
                    dsink_session_t1w_orig,
                    [("keprep_directory", "base_directory")],
                ),
                (
                    input_node,
                    dsink_session_t1w_json_orig,
                    [("keprep_directory", "base_directory")],
                ),
                (
                    collect_inputs,
                    apply_warp,
                    [("t1w_nii", "in_file")],
                ),
            ]
        )

    workflow.connect(
        [
            (
                input_node,
                apply_warp,
                [
                    ("nonlinear_warp", "field_file"),
                    ("affine_matrix", "premat"),
                ],
            ),
            (apply_warp, dsink_t1w_to_mni, [("out_file", "in_file")]),
            (
                input_node,
                dsink_t1w_to_mni,
                [("keprep_directory", "base_directory")],
            ),
            (collect_inputs, dsink_t1w_to_mni, [("t1w_nii", "source_file")]),
            (collect_inputs, dsink_t1w_to_mni_json, [("t1w_json", "in_file")]),
            (
                input_node,
                dsink_t1w_to_mni_json,
                [("keprep_directory", "base_directory")],
            ),
            (
                collect_inputs,
                dsink_t1w_to_mni_json,
                [("t1w_json", "source_file")],
            ),
        ]
    )
    return workflow
