import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu

def init_minimal_preproc_wf(name:str) -> pe.Workflow:
    """
    Create a minimal preprocessing workflow.
    """
    wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=["bids_directory","output_directory","work_directory","subject_id","session_id","do_smriprep",]),
        name="inputnode"
    )

    return wf