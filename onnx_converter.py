#!/usr/bin/env python3

import logging
from pathlib import Path

import joblib
import onnx
import onnxmltools
import skl2onnx
from onnxmltools import convert_lightgbm, convert_xgboost

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MODELS_DIR = Path("algorithms/models")
ONNX_MODELS_DIR = Path("algorithms/models_onnx")


def get_classifier_type(model_filename: str) -> str:
    if "catboost" in model_filename.lower():
        return "catboost"
    elif "lightgbm" in model_filename.lower():
        return "lightgbm"
    elif "xgboost" in model_filename.lower():
        return "xgboost"
    elif "gaussiannb" in model_filename.lower():
        return "gaussiannb"
    else:
        return "unknown"


def get_input_size(model_filename: str) -> int:
    try:
        parts = model_filename.split("_")[0].split(",")
        width = int(parts[0])
        height = int(parts[1])
        input_size = 2 * width * height
        return input_size
    except (ValueError, IndexError):
        logger.warning(f"Unable to determine input size for {model_filename}")
        return 100


def convert_catboost_to_onnx(model_path: Path, onnx_path: Path):
    logger.info(f"Converting CatBoost: {model_path.name}")

    model = joblib.load(model_path)
    input_size = get_input_size(model_path.name)

    model.save_model(str(onnx_path), format="onnx")
    logger.info(f"Converted: {onnx_path.name}")

    from onnxmltools.convert.common.data_types import (
        FloatTensorType as OnnxFloatTensorType,
    )

    initial_type = [("float_input", OnnxFloatTensorType([None, input_size]))]

    onnx_model = onnxmltools.convert_catboost(
        model, initial_types=initial_type, target_opset=12
    )
    if isinstance(onnx_model, tuple):
        onnx_model = onnx_model[0]
    onnx.save_model(onnx_model, str(onnx_path))
    logger.info(f"Converted: {onnx_path.name}")


def convert_lightgbm_to_onnx(model_path: Path, onnx_path: Path) -> None:
    logger.info(f"Converting LightGBM: {model_path.name}")

    model = joblib.load(model_path)
    input_size = get_input_size(model_path.name)
    from onnxmltools.convert.common.data_types import (
        FloatTensorType as OnnxFloatTensorType,
    )

    initial_type = [("float_input", OnnxFloatTensorType([None, input_size]))]

    onnx_model = convert_lightgbm(model, initial_types=initial_type, target_opset=12)
    onnx.save_model(onnx_model, str(onnx_path))
    logger.info(f"Converted: {onnx_path.name}")


def convert_xgboost_to_onnx(model_path: Path, onnx_path: Path):
    logger.info(f"Converting XGBoost: {model_path.name}")

    model = joblib.load(model_path)
    input_size = get_input_size(model_path.name)

    from onnxmltools.convert.common.data_types import (
        FloatTensorType as OnnxFloatTensorType,
    )

    initial_type = [("float_input", OnnxFloatTensorType([None, input_size]))]

    onnx_model = convert_xgboost(model, initial_types=initial_type, target_opset=12)
    if isinstance(onnx_model, tuple):
        onnx_model = onnx_model[0]
    onnx.save_model(onnx_model, str(onnx_path))
    logger.info(f"Converted: {onnx_path.name}")


def convert_gaussiannb_to_onnx(model_path: Path, onnx_path: Path):
    logger.info(f"Converting GaussianNB: {model_path.name}")

    model = joblib.load(model_path)
    input_size = get_input_size(model_path.name)

    from skl2onnx.common.data_types import FloatTensorType as Skl2OnnxFloatTensorType

    initial_type = [("float_input", Skl2OnnxFloatTensorType([None, input_size]))]

    onnx_model = skl2onnx.convert_sklearn(
        model, initial_types=initial_type, target_opset=12
    )
    if isinstance(onnx_model, tuple):
        onnx_model = onnx_model[0]
    onnx.save_model(onnx_model, str(onnx_path))
    logger.info(f"Converted: {onnx_path.name}")


def convert_model(model_path: Path) -> None:
    classifier_type = get_classifier_type(model_path.name)
    onnx_filename = model_path.stem + ".onnx"
    onnx_path = ONNX_MODELS_DIR / onnx_filename

    if classifier_type == "catboost":
        convert_catboost_to_onnx(model_path, onnx_path)
    elif classifier_type == "lightgbm":
        convert_lightgbm_to_onnx(model_path, onnx_path)
    elif classifier_type == "xgboost":
        convert_xgboost_to_onnx(model_path, onnx_path)
    elif classifier_type == "gaussiannb":
        convert_gaussiannb_to_onnx(model_path, onnx_path)
    else:
        logger.warning(f"unknown model type: {model_path.name}")


def main():
    if not MODELS_DIR.exists():
        logger.error(f"Models directory does not exist: {MODELS_DIR}")
        return

    ONNX_MODELS_DIR.mkdir(exist_ok=True, parents=True)
    logger.info(f"ONNX directory: {ONNX_MODELS_DIR}")
    model_files = sorted([f for f in MODELS_DIR.glob("*.model")])

    if not model_files:
        logger.warning("No .model files found")
        return

    logger.info(f"Found {len(model_files)} models to convert\n")

    for i, model_path in enumerate(model_files, 1):
        logger.info(f"[{i}/{len(model_files)}] Processing: {model_path.name}")
        convert_model(model_path)


if __name__ == "__main__":
    main()
