import multiprocessing
from typing import Any
from implementation import evaluator
from implementation import evaluator_accelerate


class Sandbox(evaluator.Sandbox):
    def __init__(self, verbose=False, numba_accelerate=True):
        self._verbose = verbose
        self._numba_accelerate = numba_accelerate

    def run(
            self,
            program: str,
            function_to_run: str,
            function_to_evolve: str,
            inputs: Any,
            test_input: str,
            timeout_seconds: int,
            **kwargs
    ) -> tuple[Any, bool]:
        dataset = inputs[test_input]
        try:
            result_queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=self._compile_and_run_function,
                args=(program, function_to_run, function_to_evolve, dataset, self._numba_accelerate, result_queue)
            )
            process.start()
            process.join(timeout=timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join()
                results = None, False
            else:
                if not result_queue.empty():
                    results = result_queue.get_nowait()
                else:
                    results = None, False

            return results
        except:
            return None, False

    def _compile_and_run_function(self, program, function_to_run, function_to_evolve, dataset, numba_accelerate,
                                  result_queue):
        try:
            if numba_accelerate:
                program = evaluator_accelerate.add_numba_decorator(
                    program=program,
                    function_to_evolve=function_to_evolve
                )
            all_globals_namespace = {}
            exec(program, all_globals_namespace)
            function_to_run = all_globals_namespace[function_to_run]
            results = function_to_run(dataset)
            if not isinstance(results, (int, float)):
                result_queue.put((None, False))
                return
            result_queue.put((results, True))
        except Exception:
            result_queue.put((None, False))
