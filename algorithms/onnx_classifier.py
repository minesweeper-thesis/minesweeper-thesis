import numpy as np
import onnxruntime as rt

from algorithms.boards.base_board import BaseBoard
from algorithms.classifiers.base_classifier import BaseClassifier


class OnnxClassifier(BaseClassifier):
    def fit(self, _: list[tuple[BaseBoard, bool]]) -> None:
        raise RuntimeError("ONNX classifier does not support training.")

    def save(self, _: str) -> None:
        raise RuntimeError("ONNX classifier does not support saving.")

    def __init__(self) -> None:
        self.session = None
        self.input_name = None
        self.output_name = None

    def classify(self, board: BaseBoard) -> float:
        if self.session is None:
            raise RuntimeError(
                "Model not loaded. Call 'load' method before classification."
            )

        model_data = board.model_input().reshape(1, -1).astype(np.float32)
        result = self.session.run([self.output_name], {self.input_name: model_data})

        output = np.array(result[0]).flatten()
        return float(output[-1])

    @classmethod
    def load(cls, filename: str) -> "OnnxClassifier":
        instance = cls()
        try:
            instance.session = rt.InferenceSession(
                filename, providers=["CPUExecutionProvider"]
            )
            instance.input_name = instance.session.get_inputs()[0].name
            instance.output_name = instance.session.get_outputs()[0].name
            return instance
        except Exception as e:
            raise RuntimeError(f"Cannot load ONNX model from file '{filename}': {e}")
