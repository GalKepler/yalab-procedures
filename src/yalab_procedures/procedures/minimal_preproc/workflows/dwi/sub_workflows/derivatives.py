import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

from yalab_procedures.interfaces.bids import DerivativesDataSink

DWI_PREPROC_BASE_ENTITIES = dict(desc="preproc", space="dwi", datatype="dwi")


def init_derivatives_wf(name: str = "derivatives_wf") -> pe.Workflow:
    """
    Build the workflow that saves derivatives.

    Parameters
    ----------
    name : str, optional
        name of the workflow (default: "derivatives_wf")

    Returns
    -------
    pe.Workflow
        the workflow
    """

    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "output_directory",
                "source_file",
                "dwi_preproc",
                "dwi_grad",
                "dwi_bvec",
                "dwi_bval",
                "dwi_json",
                "dwi_reference",
                "dwi_reference_json",
                "dwi2t1w_aff",
                "t1w2dwi_aff",
                "dwi_brain_mask",
                "sdc_report",
                "coreg_report",
            ]
        ),
        name="inputnode",
    )

    ds_sdc_report = pe.Node(
        DerivativesDataSink(
            desc="sdc",
            suffix="dwi",
            datatype="figures",
        ),
        name="ds_report_sdc",
        run_without_submitting=True,
    )
    ds_coreg_report = pe.Node(
        DerivativesDataSink(
            desc="coreg",
            suffix="dwi",
            datatype="figures",
        ),
        name="ds_coreg_report",
        run_without_submitting=True,
    )

    ds_dwi_preproc = pe.Node(
        DerivativesDataSink(
            suffix="dwi",
            compress=True,
            **DWI_PREPROC_BASE_ENTITIES,
        ),
        name="ds_dwi_preproc",
        run_without_submitting=True,
    )

    listify_gradients = pe.Node(
        niu.Merge(4),
        name="listify_associated_to_dwi",
    )

    ds_dwi_supp = pe.MapNode(
        DerivativesDataSink(
            suffix="dwi",
            **DWI_PREPROC_BASE_ENTITIES,
        ),
        iterfield=["in_file"],
        name="ds_dwi_gradients",
        run_without_submitting=True,
    )

    ds_dwiref = pe.Node(
        DerivativesDataSink(
            suffix="dwiref",
            compress=True,
            **DWI_PREPROC_BASE_ENTITIES,
        ),
        name="ds_dwiref",
        run_without_submitting=True,
    )

    ds_dwiref_json = pe.Node(
        DerivativesDataSink(
            suffix="dwiref",
            **DWI_PREPROC_BASE_ENTITIES,
        ),
        name="ds_dwiref_json",
        run_without_submitting=True,
    )

    ds_dwi_mask = pe.Node(
        DerivativesDataSink(
            suffix="mask",
            desc="brain",
            space="dwi",
            compress=True,
        ),
        name="ds_dwi_mask",
        run_without_submitting=True,
    )

    ds_dwi2t1w_aff = pe.Node(
        DerivativesDataSink(
            **{
                "from": "dwi",
                "to": "T1w",
                "mode": "image",
                "suffix": "xfm",
                "extension": "txt",
            },
        ),
        name="ds_dwi2t1w_aff",
        run_without_submitting=True,
    )

    ds_t1w2dwi_aff = pe.Node(
        DerivativesDataSink(
            **{
                "from": "T1w",
                "to": "dwi",
                "mode": "image",
                "suffix": "xfm",
                "extension": "txt",
            },
        ),
        name="ds_t1w2dwi_aff",
        run_without_submitting=True,
    )

    workflow.connect(
        [
            (
                inputnode,
                ds_sdc_report,
                [
                    ("output_directory", "base_directory"),
                    ("sdc_report", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_coreg_report,
                [
                    ("output_directory", "base_directory"),
                    ("coreg_report", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_dwi_preproc,
                [
                    ("output_directory", "base_directory"),
                    ("dwi_preproc", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                listify_gradients,
                [
                    ("dwi_grad", "in1"),
                    ("dwi_bvec", "in2"),
                    ("dwi_bval", "in3"),
                    ("dwi_json", "in4"),
                ],
            ),
            (
                listify_gradients,
                ds_dwi_supp,
                [("out", "in_file")],
            ),
            (
                inputnode,
                ds_dwi_supp,
                [
                    ("output_directory", "base_directory"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_dwiref,
                [
                    ("output_directory", "base_directory"),
                    ("dwi_reference", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_dwiref_json,
                [
                    ("output_directory", "base_directory"),
                    ("dwi_reference_json", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_dwi_mask,
                [
                    ("output_directory", "base_directory"),
                    ("dwi_brain_mask", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_dwi2t1w_aff,
                [
                    ("output_directory", "base_directory"),
                    ("dwi2t1w_aff", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
            (
                inputnode,
                ds_t1w2dwi_aff,
                [
                    ("output_directory", "base_directory"),
                    ("t1w2dwi_aff", "in_file"),
                    ("source_file", "source_file"),
                ],
            ),
        ]
    )

    return workflow
