from pathlib import Path
from glob import glob
from typing import Iterable, Dict, Optional, Tuple, List
import numpy as np
import tifffile as tiff
from tifffile import imread, imwrite
from cellpose import models, io, plot
from scipy.ndimage import gaussian_filter
import warnings
import matplotlib.pyplot as plt  # move import to top to avoid repeated imports


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


from pathlib import Path
from typing import Iterable, Optional, Tuple, Dict, List
import warnings
import inspect

import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt
from cellpose import models, plot, io


def cell_segment(
    img_dir: Path,
    out_root: Optional[Path] = None,
    model_types: Iterable[str] = ("nuclei", "cyto2"),
    channels: Tuple[int, int] = (0, 0),
    diameters: Optional[Dict[str, Optional[float]]] = None,
    *,
    # Normalization: "none" | "minmax" | "percentile"
    normalization: str = "none",
    norm_percentiles: Tuple[float, float] = (1.0, 99.0),
    # Non-2D handling (assume axis 0 is planes/channels if ndim==3)
    projection: Optional[str] = None,        # None | "max" | "mean"
    select_channel: Optional[int] = None,    # choose a slice from axis 0
    # Execution
    batch_size: Optional[int] = None,        # process in chunks; None = all at once
    gpu: bool = True,
    # Thresholds (some CP versions don’t support all of these)
    flow_threshold: Optional[float] = None,
    mask_threshold: Optional[float] = None,       # may not exist in your CP
    cellprob_threshold: Optional[float] = None,
    # Visualization
    preview_n: int = 0,
) -> Dict[str, List[Path]]:
    """
    Segment 2D TIFFs with Cellpose. Auto-adapts to the installed Cellpose
    by filtering unsupported eval() kwargs (e.g., mask_threshold).
    """
    io.logger_setup()

    # --- Resolve and validate paths ---
    img_dir = Path(img_dir).expanduser().resolve()
    if not img_dir.exists():
        raise FileNotFoundError(f"Input folder does not exist: {img_dir}")

    exts = {".tif", ".tiff"}
    files = sorted(p for p in img_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    if not files:
        raise FileNotFoundError(f"No images with {tuple(exts)} found in {img_dir}")

    if out_root is None:
        out_root = img_dir / "_cellpose_out"
    out_root = Path(out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    # --- Normalize model_types / diameters ---
    model_types = [model_types] if isinstance(model_types, str) else list(model_types)
    diameters = {} if diameters is None else dict(diameters)

    # --- GPU availability check ---
    try:
        gpu_available = models.use_gpu()
    except Exception:
        gpu_available = False
    use_gpu = bool(gpu and gpu_available)
    if gpu and not use_gpu:
        warnings.warn("GPU requested but not available; falling back to CPU.", RuntimeWarning)

    # --- Helpers ---
    def _to_float32(img: np.ndarray) -> np.ndarray:
        return img.astype(np.float32, copy=False)

    def _normalize(img: np.ndarray) -> np.ndarray:
        if normalization == "none":
            return img
        if normalization == "minmax":
            mn, mx = float(img.min()), float(img.max())
            return (img - mn) / (mx - mn) if mx > mn else np.zeros_like(img, dtype=np.float32)
        if normalization == "percentile":
            lo, hi = np.percentile(img, norm_percentiles)
            return np.clip((img - lo) / (hi - lo), 0.0, 1.0) if hi > lo else np.zeros_like(img, dtype=np.float32)
        raise ValueError(f"Unknown normalization mode: {normalization}")

    def _prepare_2d(img: np.ndarray, src_name: str) -> np.ndarray:
        if img.ndim == 2:
            return _normalize(_to_float32(img))
        if img.ndim == 3:
            arr = img
            if select_channel is not None:
                if not (0 <= select_channel < arr.shape[0]):
                    raise ValueError(f"{src_name}: select_channel={select_channel} out of range for {arr.shape}")
                arr = arr[select_channel]
            else:
                if projection is None:
                    raise ValueError(
                        f"{src_name}: not 2D (shape {img.shape}). Set select_channel or projection=('max'|'mean')."
                    )
                if projection == "max":
                    arr = arr.max(axis=0)
                elif projection == "mean":
                    arr = arr.mean(axis=0)
                else:
                    raise ValueError(f"{src_name}: unknown projection='{projection}'")
            if arr.ndim != 2:
                raise ValueError(f"{src_name}: expected 2D after selection/projection, got {arr.shape}")
            return _normalize(_to_float32(arr))
        raise ValueError(f"{src_name}: unsupported ndim={img.ndim}; expect 2D or 3D")

    def _read_image(fp: Path) -> np.ndarray:
        img = tiff.imread(str(fp))
        return _prepare_2d(img, fp.name)

    def _batched(seq, n: int):
        for i in range(0, len(seq), n):
            yield i, seq[i : i + n]

    # Filter kwargs based on installed Cellpose eval() signature
    def _cp_eval(model, imgs_chunk, *, diameter, channels,
                 flow_threshold, mask_threshold, cellprob_threshold):
        kw = {
            "diameter": diameter,
            "channels": channels,
            "flow_threshold": flow_threshold,
            "mask_threshold": mask_threshold,
            "cellprob_threshold": cellprob_threshold,
        }
        # Keep only supported parameters
        sig = inspect.signature(model.eval)
        allowed = set(sig.parameters.keys())
        kw = {k: v for k, v in kw.items() if k in allowed and v is not None}
        return model.eval(imgs_chunk, **kw)

    # Unpack Cellpose outputs across versions
    def _unpack_eval(out, n_imgs: int):
        if isinstance(out, tuple):
            if len(out) == 4:
                return out
            if len(out) == 3:
                masks_list, flows_list, styles = out
                diams = [None] * len(masks_list)
                return masks_list, flows_list, styles, diams
        masks_list = out
        flows_list = [None] * n_imgs
        styles = None
        diams = [None] * n_imgs
        return masks_list, flows_list, styles, diams

    # --- Load images (all or batched) ---
    if batch_size is None:
        imgs = [_read_image(f) for f in files]
        shapes = {im.shape for im in imgs}
        if len(shapes) > 1:
            raise ValueError(f"Not all images share the same shape: {sorted(shapes)}")
    else:
        imgs = None  # load per batch

    results: Dict[str, List[Path]] = {}

    for model_type in model_types:
        out_dir = out_root / str(model_type)
        out_dir.mkdir(parents=True, exist_ok=True)
        model = models.CellposeModel(gpu=use_gpu, model_type=model_type)

        saved_paths: List[Path] = []

        def _eval_and_save(imgs_chunk: List[np.ndarray], file_chunk: List[Path]):
            out = _cp_eval(
                model,
                imgs_chunk,
                diameter=diameters.get(model_type),
                channels=channels,
                flow_threshold=flow_threshold,
                mask_threshold=mask_threshold,
                cellprob_threshold=cellprob_threshold,
            )
            masks_list, flows_list, styles, diams_list = _unpack_eval(out, n_imgs=len(imgs_chunk))

            for i, (fp, img, masks, flows) in enumerate(zip(file_chunk, imgs_chunk, masks_list, flows_list)):
                save_path = out_dir / f"{fp.stem}_cp_{model_type}_masks.tif"
                tiff.imwrite(str(save_path), masks.astype(np.uint16), photometric="minisblack")
                saved_paths.append(save_path)

                if len(saved_paths) <= preview_n:
                    fig = plt.figure(figsize=(6, 5))
                    try:
                        flow_show = flows[0] if isinstance(flows, (list, tuple)) else flows
                        plot.show_segmentation(fig, img, masks, flow_show, channels=channels)
                    except Exception:
                        overlay = plot.mask_overlay(img, masks)
                        plt.imshow(overlay); plt.title(f"{fp.name} • {model_type}"); plt.axis("off")
                    plt.tight_layout(); plt.show(); plt.close(fig)

        if batch_size is None:
            _eval_and_save(imgs, files)
        else:
            if batch_size <= 0:
                raise ValueError("batch_size must be a positive integer")
            shape_ref = None
            for _, fchunk in _batched(files, batch_size):
                ichunk = [_read_image(f) for f in fchunk]
                shapes = {im.shape for im in ichunk}
                if len(shapes) != 1:
                    raise ValueError(f"Within-batch images have different shapes: {sorted(shapes)}")
                if shape_ref is None:
                    shape_ref = ichunk[0].shape
                elif ichunk[0].shape != shape_ref:
                    raise ValueError(f"Batches differ in shape: saw {ichunk[0].shape} vs {shape_ref}")
                _eval_and_save(ichunk, fchunk)

        results[model_type] = saved_paths

    return results
