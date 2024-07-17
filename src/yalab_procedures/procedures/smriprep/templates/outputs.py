# flake8: noqa: E501
SMRIPREP_OUTPUTS = {
    "smriprep": {
        # T1w-related outputs
        "preprocessed_T1w": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_desc-preproc_T1w.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_desc-preproc_T1w.nii.gz",
        },
        "brain_mask": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_desc-brain_mask.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_desc-brain_mask.nii.gz",
        },
        "MNI_preprocessed_T1w": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz",
        },
        "MNI_brain_mask": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
        },
        # Transformations
        "mni_to_native_transform": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5",
            "subject": "sub-{subject}/anat/sub-{subject}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5",
        },
        "native_to_mni_transform": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5",
            "subject": "sub-{subject}/anat/sub-{subject}_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5",
        },
        "fsnative_to_native_transform": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_from-fsnative_to-T1w_mode-image_xfm.txt",
            "subject": "sub-{subject}/anat/sub-{subject}_from-fsnative_to-T1w_mode-image_xfm.txt",
        },
        "native_to_fsnative_transform": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_from-T1w_to-fsnative_mode-image_xfm.txt",
            "subject": "sub-{subject}/anat/sub-{subject}_from-T1w_to-fsnative_mode-image_xfm.txt",
        },
        # Segmentation outputs
        "segmentation": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_desc-aparcaseg_dseg.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_desc-aparcaseg_dseg.nii.gz",
        },
        # Probabilistic segmentation outputs
        "probseg_gm": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_label-GM_probseg.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_label-GM_probseg.nii.gz",
        },
        "probseg_wm": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_label-WM_probseg.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_label-WM_probseg.nii.gz",
        },
        "probseg_csf": {
            "session": "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_label-CSF_probseg.nii.gz",
            "subject": "sub-{subject}/anat/sub-{subject}_label-CSF_probseg.nii.gz",
        },
        # Add other necessary output paths as needed
    },
    "freesurfer": {
        "fsaverage": "fsaverage/mri/brain.mgz",
        "T1w": "sub-{subject}/mri/T1.mgz",
        "brainmask": "sub-{subject}/mri/brainmask.mgz",
        "brain": "sub-{subject}/mri/brain.mgz",
        "wm": "sub-{subject}/mri/wm.mgz",
        "lh_pial": "sub-{subject}/surf/lh.pial",
        "rh_pial": "sub-{subject}/surf/rh.pial",
    },
}
