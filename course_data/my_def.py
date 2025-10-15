!pip install "cellpose<4"

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


def cell_segment(
    img_dir: Path,
    out_root: Optional[Path] = None,
    model_types: Iterable[str] = ("cyto2", "nuclei"),
    channels: Tuple[int, int] = (0, 0),
    diameter_px: Optional[float] = None,
    normalize01: bool = False,
    gpu: bool = True,
    preview_n: int = 0,
    save_previews: bool = False
) -> Dict[str, List[Path]]:
    io.logger_setup()

    if isinstance(model_types, str):
        model_types = [model_types]

    img_dir = Path(img_dir).expanduser().resolve()
    if out_root is None:
        out_root = img_dir / "_cellpose_out"
    out_root.mkdir(parents=True, exist_ok=True)

    exts = {".tif", ".tiff"}
    files = sorted(p for p in img_dir.rglob("*") if p.suffix.lower() in exts)
    if not files:
        raise FileNotFoundError(f"No .tif/.tiff files found in {img_dir}")

    def read_2d(path: Path) -> np.ndarray:
        arr = tiff.imread(str(path))
        if arr.ndim != 2:
            raise ValueError(f"Expected 2D TIFF, got shape {arr.shape}: {path.name}")
        if normalize01:
            arr = (arr - arr.min()) / (arr.ptp() + 1e-8)
        return arr.astype(np.float32)

    imgs = [read_2d(f) for f in files]
    results: Dict[str, List[Path]] = {}

    for model_type in model_types:
        print(f"[INFO] Running Cellpose model: {model_type}")
        # Either model works; CellposeModel is recommended in v3+
        model = models.CellposeModel(gpu=gpu, model_type=model_type)

        out = model.eval(imgs, diameter=diameter_px, channels=channels)

        # ---- Robustly handle different return signatures ----
        if isinstance(out, tuple):
            if len(out) == 4:
                masks_list, flows_list, styles, diams = out
            elif len(out) == 3:
                masks_list, flows_list, styles = out
                diams = [diameter_px] * len(imgs)
            else:
                masks_list = out[0]
                flows_list = out[1] if len(out) > 1 else [None] * len(imgs)
                diams = [diameter_px] * len(imgs)
        else:
            masks_list = out
            flows_list = [None] * len(imgs)
            diams = [diameter_px] * len(imgs)
        # -----------------------------------------------------

        out_dir = out_root / model_type
        out_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: List[Path] = []

        for i, (fp, img, masks, flow) in enumerate(zip(files, imgs, masks_list, flows_list)):
            save_path = out_dir / f"{fp.stem}_cp_{model_type}_mask.tif"
            tiff.imwrite(str(save_path), masks.astype(np.uint16), photometric="minisblack")
            saved_paths.append(save_path)

            if i < preview_n:
                fig = plt.figure(figsize=(6, 5))
                try:
                    flow_show = flow[0] if isinstance(flow, (list, tuple)) else flow
                    plot.show_segmentation(fig, img, masks, flow_show, channels=channels)
                except Exception:
                    # Fallback overlay if flow structure differs
                    overlay = plot.mask_overlay(img, masks)
                    plt.imshow(overlay, cmap=None)
                    plt.title(f"{fp.name} • {model_type}")
                    plt.axis("off")
                plt.tight_layout()
                if save_previews:
                    plt.savefig(out_dir / f"{fp.stem}_cp_{model_type}_preview.png", dpi=150)
                plt.show()
                plt.close(fig)

        results[model_type] = saved_paths

    return results


"""
from pathlib import Path

# For nuclei
cell_segment(
    img_dir=Path("/Users/romankoval/data/flat_dark_apply"),
    out_root=Path("/Users/romankoval/data/cyto"),
    model_types=["nuclei"],
    channels=(0, 0),
    diameter_px=30,
    normalize01=False,
    gpu=True,
    preview_n=3,
    save_previews=True
)


cell_segment(
    img_dir=Path("/Users/romankoval/data/flat_dark_apply"),
    out_root=Path("/Users/romankoval/data/cyto"),
    model_types=["cyto2"],
    channels=(0, 0),
    diameter_px=90,
    normalize01=False,
    gpu=True,
    preview_n=3,
    save_previews=True
)
"""