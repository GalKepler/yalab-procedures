from __future__ import annotations

from typing import Optional

from heudiconv.utils import SeqInfo


def create_key(
    template: Optional[str],
    outtype: tuple[str, ...] = ("nii.gz", "json"),
    annotation_classes: None = None,
) -> tuple[str, tuple[str, ...], None]:
    if template is None or not template:
        raise ValueError("Template must be a valid format string")
    return (template, outtype, annotation_classes)


def infotodict(
    seqinfo: list[SeqInfo],
) -> dict[tuple[str, tuple[str, ...], None], list]:
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    session: scan index for longitudinal acq
    """
    t1_corrected = create_key(
        "{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_ce-corrected_T1w"
    )
    t1_uncorrected = create_key(
        "{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_ce-uncorrected_T1w"
    )
    t2_corrected = create_key(
        "{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_ce-corrected_T2w"
    )
    t2_uncorrected = create_key(
        "{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_ce-uncorrected_T2w"
    )
    flair = create_key(
        "{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_FLAIR"
    )
    dwi_ap = create_key(
        "{bids_subject_session_dir}/dwi/{bids_subject_session_prefix}_dir-AP_dwi"
    )
    dwi_pa = create_key(
        "{bids_subject_session_dir}/dwi/{bids_subject_session_prefix}_dir-PA_dwi"
    )
    dwi_ap_sbref = create_key(
        "{bids_subject_session_dir}/dwi/{bids_subject_session_prefix}_dir-AP_sbref"
    )
    dwi_pa_sbref = create_key(
        "{bids_subject_session_dir}/dwi/{bids_subject_session_prefix}_dir-PA_sbref"
    )
    fmap_ap = create_key(
        "{bids_subject_session_dir}/fmap/{bids_subject_session_prefix}_acq-func_dir-AP_epi"
    )
    fmap_pa = create_key(
        "{bids_subject_session_dir}/fmap/{bids_subject_session_prefix}_acq-func_dir-PA_epi"
    )
    fmap_task_ap = create_key(
        "{bids_subject_session_dir}/fmap/{bids_subject_session_prefix}_acq-task_dir-AP_epi"
    )
    fmap_task_pa = create_key(
        "{bids_subject_session_dir}/fmap/{bids_subject_session_prefix}_acq-task_dir-PA_epi"
    )
    rest = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-rest_bold"
    )
    rest_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-rest_sbref"
    )
    # Functional tasks
    bjj1 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj1_bold"
    )
    bjj1_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj1_sbref"
    )
    bjj2 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj2_bold"
    )
    bjj2_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj2_sbref"
    )
    bjj3 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj3_bold"
    )
    bjj3_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-bjj3_sbref"
    )
    climbing1 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing1_bold"
    )
    climbing1_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing1_sbref"
    )
    climbing2 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing2_bold"
    )
    climbing2_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing2_sbref"
    )
    climbing3 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing3_bold"
    )
    climbing3_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-climbing3_sbref"
    )
    music1 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music1_bold"
    )
    music1_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music1_sbref"
    )
    music2 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music2_bold"
    )
    music2_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music2_sbref"
    )
    music3 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music3_bold"
    )
    music3_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-music3_sbref"
    )
    movement1 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-movement1_bold"
    )
    movement1_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-movement1_sbref"
    )
    movement2 = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-movement2_bold"
    )
    movement2_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-movement2_sbref"
    )
    emotionalnback = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-emotionalnback_bold"
    )
    emotionalnback_sbref = create_key(
        "{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-emotionalnback_sbref"
    )

    info: dict[tuple[str, tuple[str, ...], None], list] = {
        t1_corrected: [],
        t1_uncorrected: [],
        t2_corrected: [],
        t2_uncorrected: [],
        flair: [],
        dwi_ap: [],
        dwi_pa: [],
        dwi_ap_sbref: [],
        dwi_pa_sbref: [],
        fmap_ap: [],
        fmap_pa: [],
        fmap_task_ap: [],
        fmap_task_pa: [],
        rest: [],
        rest_sbref: [],
        bjj1: [],
        bjj1_sbref: [],
        bjj2: [],
        bjj2_sbref: [],
        bjj3: [],
        bjj3_sbref: [],
        climbing1: [],
        climbing1_sbref: [],
        climbing2: [],
        climbing2_sbref: [],
        climbing3: [],
        climbing3_sbref: [],
        music1: [],
        music1_sbref: [],
        music2: [],
        music2_sbref: [],
        music3: [],
        music3_sbref: [],
        movement1: [],
        movement1_sbref: [],
        movement2: [],
        movement2_sbref: [],
        emotionalnback: [],
        emotionalnback_sbref: [],
    }

    for s in seqinfo:
        if "T1w_MPRAGE" in s.protocol_name:
            print(s.image_type)
            if "NORM" in s.image_type:
                info[t1_corrected].append(s.series_id)
            else:
                info[t1_uncorrected].append(s.series_id)
        elif "T2w_SPC" in s.protocol_name:
            if "NORM" in s.image_type:
                info[t2_corrected].append(s.series_id)
            else:
                info[t2_uncorrected].append(s.series_id)
        elif "t2_tirm_tra_dark-fluid_FLAIR" in s.protocol_name:
            info[flair].append(s.series_id)
        elif (
            "dMRI_MB4_185dirs_d15D45_AP" in s.protocol_name
            or "ep2d_d15.5D60_MB3_AP" in s.protocol_name
        ):
            info[dwi_ap].append(s.series_id)
        elif (
            "dMRI_MB4_6dirs_d15D45_PA" in s.protocol_name
            or "ep2d_d15.5D60_MB3_PA" in s.protocol_name
        ):
            info[dwi_pa].append(s.series_id)
        elif "dMRI_MB4_185dirs_d15D45_AP_SBRef" in s.protocol_name:
            info[dwi_ap_sbref].append(s.series_id)
        elif "dMRI_MB4_6dirs_d15D45_PA_SBRef" in s.protocol_name:
            info[dwi_pa_sbref].append(s.series_id)
        elif (
            "SpinEchoFieldMap_AP" in s.protocol_name
            or "SE_rsfMRI_FieldMap_AP" in s.protocol_name
        ):
            info[fmap_ap].append(s.series_id)
        elif (
            "SpinEchoFieldMap_PA" in s.protocol_name
            or "SE_rsfMRI_FieldMap_PA" in s.protocol_name
        ):
            info[fmap_pa].append(s.series_id)
        if "sbref" in s.series_description.lower():
            if "rsfMRI_AP" in s.protocol_name:
                info[rest_sbref].append(s.series_id)
            elif "fMRI_BJJ1_AP" in s.protocol_name:
                info[bjj1_sbref].append(s.series_id)
            elif "fMRI_BJJ2_AP" in s.protocol_name:
                info[bjj2_sbref].append(s.series_id)
            elif "fMRI_BJJ3_AP" in s.protocol_name:
                info[bjj3_sbref].append(s.series_id)
            elif "fMRI_Climbing1_AP" in s.protocol_name:
                info[climbing1_sbref].append(s.series_id)
            elif "fMRI_Climbing2_AP" in s.protocol_name:
                info[climbing2_sbref].append(s.series_id)
            elif "fMRI_Climbing3_AP" in s.protocol_name:
                info[climbing3_sbref].append(s.series_id)
            elif "fMRI_Music1_AP" in s.protocol_name:
                info[music1_sbref].append(s.series_id)
            elif "fMRI_Music2_AP" in s.protocol_name:
                info[music2_sbref].append(s.series_id)
            elif "fMRI_Music3_AP" in s.protocol_name:
                info[music3_sbref].append(s.series_id)
            elif "fMRI_Music_Movement1_AP" in s.protocol_name:
                info[movement1_sbref].append(s.series_id)
            elif "fMRI_Music_Movement2_AP" in s.protocol_name:
                info[movement2_sbref].append(s.series_id)
            elif "fMRI_EmotionalNBack_AP" in s.protocol_name:
                info[emotionalnback_sbref].append(s.series_id)
        else:
            if "rsfMRI_AP" in s.protocol_name:
                info[rest].append(s.series_id)
            elif "fMRI_BJJ1_AP" in s.protocol_name:
                info[bjj1].append(s.series_id)
            elif "fMRI_BJJ2_AP" in s.protocol_name:
                info[bjj2].append(s.series_id)
            elif "fMRI_BJJ3_AP" in s.protocol_name:
                info[bjj3].append(s.series_id)
            elif "fMRI_Climbing1_AP" in s.protocol_name:
                info[climbing1].append(s.series_id)
            elif "fMRI_Climbing2_AP" in s.protocol_name:
                info[climbing2].append(s.series_id)
            elif "fMRI_Climbing3_AP" in s.protocol_name:
                info[climbing3].append(s.series_id)
            elif "fMRI_Music1_AP" in s.protocol_name:
                info[music1].append(s.series_id)
            elif "fMRI_Music2_AP" in s.protocol_name:
                info[music2].append(s.series_id)
            elif "fMRI_Music3_AP" in s.protocol_name:
                info[music3].append(s.series_id)
            elif "fMRI_Music_Movement1_AP" in s.protocol_name:
                info[movement1].append(s.series_id)
            elif "fMRI_Music_Movement2_AP" in s.protocol_name:
                info[movement2].append(s.series_id)
            elif "fMRI_EmotionalNBack_AP" in s.protocol_name:
                info[emotionalnback].append(s.series_id)

    return info
