from pathlib import Path
from glob import glob
from typing import Iterable, Dict, Optional, Tuple, List
import numpy as np
import tifffile as tiff
from tifffile import imread, imwrite
from cellpose import models, io, plot
from scipy.ndimage import gaussian_filter



def estimate_flat_dark(image_paths, sigma_px=60):
    """Estimate flat-field (multiplicative) and dark (additive) from many frames."""
    stack = [imread(p).astype(np.float32) for p in image_paths]
    med  = np.median(np.stack(stack, axis=0), axis=0)   # robust to cells moving
    dark = np.percentile(np.stack(stack, axis=0), 1, axis=0)  # near-min as additive
    flat = gaussian_filter(med, sigma=sigma_px)         # smooth illumination field
    flat = np.clip(flat, np.median(flat[flat>0])*0.1, None)   # guard against zeros
    # normalize flat so its median is 1
    flat /= np.median(flat)
    return flat.astype(np.float32), dark.astype(np.float32)

def apply_correction(img, flat, dark):
    corr = (img.astype(np.float32) - dark) / flat
    # rescale back to original dtype range
    corr -= corr.min()
    corr *= (np.iinfo(img.dtype).max / max(1e-6, corr.max()))

    return corr.astype(np.uint16)




def cell_segment(
    img_dir: Path,
    out_root: Optional[Path] = None,
    model_types: Iterable[str] = ("nuclei",),         # ("cyto", "nuclei") to run both
    channels: Tuple[int, int] = (0, 0),               # 2D grayscale
    diameters: Optional[Dict[str, Optional[float]]] = None,  # e.g., {"nuclei": 14, "cyto": 30}
    normalize01: bool = True,                         # per-image min-max → [0,1]
    gpu: bool = True,
    preview_n: int = 0                                # show first N overlays per model
) -> Dict[str, List[Path]]:
    """
    Segment 2D TIF/TIFF images with Cellpose.

    Parameters
    ----------
    img_dir : Path
        Folder with input *.tif/*.tiff (searched recursively).
    out_root : Path | None
        Where to write outputs; default = img_dir/'_cellpose_out'.
    model_types : iterable of {'cyto','nuclei'}
        Which Cellpose models to run.
    channels : (int,int)
        Cellpose channel mapping; for single-channel grayscale keep (0,0).
    diameters : dict[str, float|None] | None
        Optional per-model diameter; None lets Cellpose estimate.
    normalize01 : bool
        If True, min-max scale each image to [0,1].
    gpu : bool
        Enable GPU if available.
    preview_n : int
        If >0, show quick overlays for first N images per model.

    Returns
    -------
    outputs : dict
        Map model_type -> list of paths to saved mask TIFFs.
    """
    io.logger_setup()

    img_dir = Path(img_dir).expanduser().resolve()
    if not img_dir.exists():
        raise FileNotFoundError(f"Input folder does not exist: {img_dir}")

    exts = {".tif", ".tiff"}
    files = sorted(p for p in img_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    if not files:
        raise FileNotFoundError(f"No images with {tuple(exts)} found in {img_dir}")

    if out_root is None:
        out_root = img_dir / "_cellpose_out"
    out_root.mkdir(parents=True, exist_ok=True)

    if diameters is None:
        diameters = {}
    model_types = tuple(model_types)

    def read_2d(fp: Path) -> np.ndarray:
        img = tiff.imread(str(fp))
        if img.ndim != 2:
            raise ValueError(f"{fp.name} is not 2D; got shape {img.shape}")
        if normalize01:
            img = img.astype(np.float32, copy=False)
            mn, mx = float(img.min()), float(img.max())
            if mx > mn:
                img = (img - mn) / (mx - mn)
            else:
                img = np.zeros_like(img, dtype=np.float32)
        return img

    def unpack_eval(out, n_imgs):
        # Handle different Cellpose versions (3 vs 4 return values vs just masks)
        if isinstance(out, tuple):
            if len(out) == 4:
                return out  # masks_list, flows_list, styles, diams
            if len(out) == 3:
                masks_list, flows_list, styles = out
                diams = [None] * len(masks_list)
                return masks_list, flows_list, styles, diams
        masks_list = out
        flows_list = [None] * n_imgs
        styles = None
        diams = [None] * n_imgs
        return masks_list, flows_list, styles, diams

    # Load all images (keeps code simple; for huge sets, stream per-image instead)
    imgs = [read_2d(f) for f in files]

    results: Dict[str, List[Path]] = {}

    for model_type in model_types:
        out_dir = out_root / model_type
        out_dir.mkdir(parents=True, exist_ok=True)

        model = models.CellposeModel(gpu=gpu, model_type=model_type)
        out = model.eval(
            imgs,
            diameter=diameters.get(model_type),
            flow_threshold=None,
            channels=channels
        )
        masks_list, flows_list, styles, diams = unpack_eval(out, n_imgs=len(imgs))

        saved_paths: List[Path] = []
        for i, (fp, img, masks, flows) in enumerate(zip(files, imgs, masks_list, flows_list)):
            save_path = out_dir / f"{fp.stem}_cp_{model_type}_masks.tif"
            tiff.imwrite(str(save_path), masks.astype(np.uint16), photometric="minisblack")
            saved_paths.append(save_path)

            if i < preview_n:
                import matplotlib.pyplot as plt
                try:
                    flow_show = flows[0] if isinstance(flows, (list, tuple)) else flows
                    plot.show_segmentation(plt.gcf(), img, masks, flow_show, channels=channels)
                except Exception:
                    overlay = plot.mask_overlay(img, masks)
                    plt.imshow(overlay); plt.title(f"{fp.name} • {model_type}"); plt.axis("off")
                plt.tight_layout(); plt.show()

        results[model_type] = saved_paths

    return results

"""
from pathlib import Path

outputs = cell_segment(
    img_dir=Path("/path/to/2D_tifs"),
    model_types=("cyto","nuclei"),
    diameters={"nuclei": 14, "cyto": 30},  # or leave None to auto
    channels=(0,0),
    gpu=True,
    preview_n=2
)
print({k: len(v) for k,v in outputs.items()})
"""