import tempfile
from pathlib import Path

import pytest
from traits.trait_errors import TraitError

from yalab_procedures.procedures.smriprep import SmriprepProcedure


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def smriprep_procedure(temp_dir):
    input_dir = temp_dir / "input"
    output_dir = temp_dir / "output"
    logging_dir = temp_dir / "logs"
    working_directory = temp_dir / "working"
    (input_dir / "sub-test").mkdir(exist_ok=True, parents=True)
    for subdir in [
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
        "README",
    ]:
        (input_dir / subdir).touch()
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    logging_dir.mkdir(parents=True, exist_ok=True)
    working_directory.mkdir(parents=True, exist_ok=True)

    config = {
        "input_directory": str(input_dir),
        "output_directory": str(output_dir),
        "logging_directory": str(logging_dir),
        "work_directory": str(working_directory),
        "participant_label": "test",
    }
    procedure = SmriprepProcedure(**config)
    return procedure


def test_smriprep_procedure_init(smriprep_procedure):
    assert Path(smriprep_procedure.inputs.input_directory).exists()
    assert Path(smriprep_procedure.inputs.output_directory).exists()
    assert Path(smriprep_procedure.inputs.logging_directory).exists()
    assert Path(smriprep_procedure.inputs.work_directory).exists()
    assert smriprep_procedure.inputs.force == False  # noqa: E712
    assert smriprep_procedure.inputs.participant_label == "test"


def test_command_line_construction(smriprep_procedure):
    cmd = smriprep_procedure.cmdline
    expected_cmd = (
        f"docker run --rm "
        f"-v {smriprep_procedure.inputs.input_directory}:/data:ro "
        f"-v {smriprep_procedure.inputs.output_directory}:/out "
        f"-v {smriprep_procedure.inputs.work_directory}:/work "
        f"nipreps/smriprep:0.15.0 "
        "/data /out participant --participant_label test --work-dir /work"
    ).strip()
    assert cmd == expected_cmd


def test_failed_fs_license(smriprep_procedure):
    with pytest.raises(TraitError):
        smriprep_procedure.inputs.fs_license_file = "/nonexistent/license.txt"


def test_failed_execution(smriprep_procedure):
    with pytest.raises(Exception):
        smriprep_procedure.run()


def test_list_outputs(smriprep_procedure):
    outputs = smriprep_procedure._list_outputs()
    assert outputs["output_directory"] == str(
        smriprep_procedure.inputs.output_directory
    )


def test_prepare_inputs(smriprep_procedure):
    smriprep_procedure.setup_logging()
    temp_bids = smriprep_procedure._prepare_inputs()
    assert Path(temp_bids).exists()
    assert smriprep_procedure.inputs.input_directory == str(temp_bids)
