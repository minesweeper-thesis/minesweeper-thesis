from algorithms.heuristics.base_heuristic import BaseHeuristic
from algorithms.boards.base_board import BaseBoard
from algorithms.boards.semi_random_board import SemiRandomBoard
from algorithms.classifiers.base_classifier import BaseClassifier
from algorithms.boards.functions.all_fields import all_fields
import math
import random

# change c to class variable


class Node:
    def __init__(
        self,
        mined_fields: list[tuple[int, int]],
        parent: "Node",
        children: list["Node"],
        c: float,
    ) -> None:
        self.accumulated_reward: float = 0
        self.visits: int = 0
        self.parent: Node = parent
        self.children: list[Node] = children
        self.mined_fields = mined_fields
        self.c = c

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def add_reward(self, score: float) -> None:
        self.visits += 1
        self.accumulated_reward += score

    def ucb(self) -> float:
        return self.accumulated_reward / self.visits + self.c * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )


class MCTSHeuristic(BaseHeuristic):
    def __init__(
        self,
        classifier: BaseClassifier,
        rows: int,
        columns: int,
        start_field: tuple[int, int],
        mine_count: int,
        tries: int,
        depth: int,
        simulation_count: int,
        c: int = math.sqrt(2),
    ) -> None:
        BaseHeuristic.__init__(self, classifier, rows, columns, start_field, mine_count)
        self.tries = tries
        self.depth = depth
        self.c = c
        self.simulation_count = simulation_count

    def _expand(self, node: Node) -> Node:
        if len(node.mined_fields) == self.mine_count:
            return node

        fields = sorted(
            all_fields(self.rows, self.columns, self.start_field, node.mined_fields)
        )[: -(self.mine_count - len(node.mined_fields))]
        available_fields = [
            field
            for field in fields
            if not node.mined_fields or field > node.mined_fields[-1]
        ]
        for field in available_fields:
            node.children.append(Node(node.mined_fields + [field], node, [], self.c))

        return random.choice(node.children)

    def _rollout(self, node: Node) -> float:
        sum_rollout = 0.0

        for _ in range(self.simulation_count):
            board = SemiRandomBoard(
                self.rows,
                self.columns,
                self.start_field,
                self.mine_count,
                node.mined_fields,
            )

            sum_rollout += self.classifier.classify(board)

        return sum_rollout / self.simulation_count

    def _propagate(self, score: float, node: Node) -> None:
        while node:
            node.add_reward(score)
            node = node.parent

    def _select(self, node: Node) -> Node:
        if node.is_leaf():
            return node

        unvisited_nodes = [child for child in node.children if not child.visits]
        if unvisited_nodes:
            return random.choice(unvisited_nodes)

        return self._select(max(node.children, key=lambda n: n.ucb()))

    def _mcts(self, root: Node):
        for _ in range(self.tries):
            select_node = self._select(root)
            expanded_node = self._expand(select_node)
            reward = self._rollout(expanded_node)
            self._propagate(reward, expanded_node)

    def run(self) -> BaseBoard:
        root = Node([], None, [], self.c)

        for i in range(self.mine_count):
            if i % self.depth == 0 or not root.children:
                self._mcts(root)
            root = max(root.children, key=lambda n: n.visits)

        return BaseBoard(
            self.rows,
            self.columns,
            self.start_field,
            self.mine_count,
            root.mined_fields,
        )
