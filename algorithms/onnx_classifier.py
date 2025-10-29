import numpy as np
import onnxruntime as rt

from algorithms.boards.board import Board
from algorithms.classifiers.classifier import Classifier


class OnnxClassifier(Classifier):
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        raise NotImplementedError()

    def save(self, filename: str) -> None:
        raise NotImplementedError()

    def __init__(self) -> None:
        self.session = None
        self.input_name = None
        self.output_name = None

    def classify(self, board: Board) -> float:
        if self.session is None:
            raise RuntimeError(
                "Model nie został załadowany. Najpierw załaduj model za pomocą load()."
            )

        # Przygotuj dane wejściowe
        # model_input() zwraca (2, rows, columns), musimy spłaszczyć to do (1, 2*rows*columns)
        model_data = board.model_input().reshape(1, -1).astype(np.float32)

        # Uruchom inference
        result = self.session.run([self.output_name], {self.input_name: model_data})

        # ONNX zwraca output w różnych formatach zależnie od typu modelu
        # Dla klasyfikacji binarnej zwracamy prawdopodobieństwo klasy 1
        output = result[0]

        if isinstance(output, np.ndarray):
            # Jeśli output to tablica z prawdopodobieństwami [prob_0, prob_1]
            if output.shape[-1] == 2:
                return float(output[0, 1])
            # Jeśli to pojedyncze prawdopodobieństwo
            elif output.ndim == 2 and output.shape[1] == 1:
                return float(output[0, 0])
            # Fallback - zwróć pierwszy element
            else:
                return float(output.flat[0])
        else:
            return float(output)

    def load(self, filename: str) -> None:
        try:
            # Załaduj sesję ONNX Runtime
            self.session = rt.InferenceSession(
                filename, providers=["CPUExecutionProvider"]
            )

            # Pobierz nazwy wejścia i wyjścia
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

        except Exception as e:
            raise RuntimeError(
                f"Nie można załadować modelu ONNX z pliku '{filename}': {e}"
            )
