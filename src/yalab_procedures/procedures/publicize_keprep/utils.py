from pathlib import Path


def get_file(
    input_directory: Path,
    participant_label: str,
    regex: str,
    is_dwi: bool = False,
    extension: str = ".nii.gz",
    get_associated_files: bool = True,
):
    """
    Collect an image and associated files.

    Parameters
    ----------
    input_directory : Path
        Keprep directory
    participant_label : str
        Participant label
    regex : str
        Regular expression to match the file
    is_dwi : bool, optional
        _description_, by default False

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    FileNotFoundError
        _description_
    FileNotFoundError
        _description_
    """
    print(f"searching for sub-{participant_label}*{regex}{extension}")
    nifti = list(input_directory.glob(f"sub-{participant_label}*{regex}{extension}"))
    if len(nifti) == 0:
        raise FileNotFoundError(f"No image found in {input_directory}.")
    nifti = nifti[0]
    if get_associated_files:
        json_file = nifti.with_name(nifti.name.replace(".nii.gz", ".json"))
        if is_dwi:
            bval = nifti.with_name(nifti.name.replace(".nii.gz", ".bval"))
            bvec = nifti.with_name(nifti.name.replace(".nii.gz", ".bvec"))
            if not bval.exists():
                raise FileNotFoundError(f"No bval file found for {nifti}.")
            if not bvec.exists():
                raise FileNotFoundError(f"No bvec file found for {nifti}.")
            return nifti, json_file, bval, bvec
        return nifti, json_file
    return nifti
