import nipype.pipeline.engine as pe
from nipype.interfaces.utility import Function, IdentityInterface, Merge

from yalab_procedures.interfaces.data_grabber.data_grabber import YALabBidsQuery
from yalab_procedures.procedures.mrtrix_preprocessing.workflows.prepare_inputs.bids_to_input import (
    BIDS_TO_INPUT_MAPPING,
)


def setup_output_directory(output_directory: str, subject_id: str, session_id: str):
    """
    Setup the output directory
    """
    from pathlib import Path

    MRTRIX_SUBDIRECTORIES = ["config_files", "raw_data"]
    result = {}
    output_directory = Path(output_directory) / subject_id / session_id
    for subdirectory in MRTRIX_SUBDIRECTORIES:
        (output_directory / subdirectory).mkdir(parents=True, exist_ok=True)
        result[subdirectory] = str(output_directory / subdirectory)

    return result.get("raw_data"), result.get("config_files")


def copy_file_to_output_directory(
    in_file: str, output_directory: str, out_name: str = None
):
    """
    Copy a file to the output directory
    """
    from pathlib import Path
    from shutil import copyfile

    in_file = Path(in_file)
    output_directory = Path(output_directory)
    out_file = (
        output_directory / out_name if out_name else output_directory / in_file.name
    )

    copyfile(in_file, out_file)

    return out_file


def prepare_inputs_wf():
    """
    Prepare inputs workflow
    """

    # Create the workflow
    prepare_inputs_wf = pe.Workflow(name="prepare_inputs_wf")

    # Create the input node
    input_node = pe.Node(
        IdentityInterface(
            fields=["subject_id", "session_id", "input_directory", "output_directory"]
        ),
        name="input_node",
    )

    # Create the setup output directory node
    setup_output_directory_node = pe.Node(
        Function(
            function=setup_output_directory,
            input_names=["output_directory", "subject_id", "session_id"],
            output_names=["raw_data_output_directory", "config_files_output_directory"],
        ),
        name="setup_output_directory_node",
    )

    # Connect input_node to setup_output_directory_node
    prepare_inputs_wf.connect(
        input_node, "output_directory", setup_output_directory_node, "output_directory"
    )
    prepare_inputs_wf.connect(
        input_node, "subject_id", setup_output_directory_node, "subject_id"
    )
    prepare_inputs_wf.connect(
        input_node, "session_id", setup_output_directory_node, "session_id"
    )

    # Create the bids query node
    bids_query_node = pe.Node(
        YALabBidsQuery(raise_on_empty=False), name="bids_query_node"
    )
    prepare_inputs_wf.connect(
        input_node, "input_directory", bids_query_node, "base_dir"
    )
    prepare_inputs_wf.connect(input_node, "subject_id", bids_query_node, "subject")
    prepare_inputs_wf.connect(input_node, "session_id", bids_query_node, "session")

    # Create the copy raw data node - a map node that copies the raw data to the output directory
    copy_raw_data_node = pe.MapNode(
        Function(
            function=copy_file_to_output_directory,
            input_names=["in_file", "output_directory", "out_name"],
            output_names=["out_file"],
        ),
        name="copy_raw_data_node",
        iterfield=["in_file", "out_name"],
    )

    # Connecting setup output directory node

    prepare_inputs_wf.connect(
        setup_output_directory_node,
        "raw_data_output_directory",
        copy_raw_data_node,
        "output_directory",
    )

    # Ensure listify nodes are used to create list inputs for the MapNode iterfields
    listify_bids_query_outputs_node = pe.Node(
        Merge(len(BIDS_TO_INPUT_MAPPING)), name="listify_bids_query_outputs_node"
    )
    listify_copy_data_inputs_node = pe.Node(
        Merge(len(BIDS_TO_INPUT_MAPPING)), name="listify_copy_data_inputs_node"
    )

    # Populate listify nodes
    for i, (src, dest) in enumerate(BIDS_TO_INPUT_MAPPING.items()):
        prepare_inputs_wf.connect(
            bids_query_node, src, listify_bids_query_outputs_node, f"in{i+1}"
        )
        listify_copy_data_inputs_node.inputs.set(**{f"in{i+1}": dest})

    # Connect the listify nodes to the copy raw data node
    prepare_inputs_wf.connect(
        listify_bids_query_outputs_node, "out", copy_raw_data_node, "in_file"
    )
    prepare_inputs_wf.connect(
        listify_copy_data_inputs_node, "out", copy_raw_data_node, "out_name"
    )

    return prepare_inputs_wf