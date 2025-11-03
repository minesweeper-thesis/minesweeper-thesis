import numpy as np
import onnxruntime as rt

from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class OnnxClassifier(Classifier):
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        raise RuntimeError("ONNX classifier does not support training.")

    def save(self, filename: str) -> None:
        raise RuntimeError("ONNX classifier does not support saving.")

    def __init__(self) -> None:
        self.session = None
        self.input_name = None
        self.output_name = None

    def classify(self, board: Board) -> float:
        if self.session is None:
            raise RuntimeError(
                "Model not loaded. Call 'load' method before classification."
            )

        model_data = board.model_input().reshape(1, -1).astype(np.float32)
        result = self.session.run([self.output_name], {self.input_name: model_data})
        output = result[0]

        if isinstance(output, np.ndarray):
            if output.shape[-1] == 2:
                return float(output[0, 1])
            elif output.ndim == 2 and output.shape[1] == 1:
                return float(output[0, 0])
            else:
                return float(output.flat[0])
        else:
            return float(output)

    def load(self, filename: str) -> None:
        try:
            self.session = rt.InferenceSession(
                filename, providers=["CPUExecutionProvider"]
            )

            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

        except Exception as e:
            raise RuntimeError(f"Cannot load ONNX model from file '{filename}': {e}")
