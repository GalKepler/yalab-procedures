import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from neuroflow.structural.smriprep_runner import SMRIPrepRunner

def init_anatomical_wf(name: str = "anatomical_wf") -> pe.Workflow:
    """
    Initialize the anatomical workflow.

    Parameters
    ----------
    name : str, optional
        Name of the workflow, by default "anatomical_wf"

    Returns
    -------
    pe.Workflow
        Anatomical workflow
    """
    wf = pe.Workflow(name=name)

