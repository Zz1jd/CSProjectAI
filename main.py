from implementation import funsearch
from implementation import config
from implementation import sampler as sampler_lib
from sandbox import Sandbox
from specification import specification
from dataset import load_cvrp_dataset


RUNTIME_DEFAULTS = config.RuntimeDefaults()
COMPARE_MAX_SAMPLE_NUMS = RUNTIME_DEFAULTS.compare_max_sample_nums


def validate_runtime_config(config_obj: config.Config) -> None:
    if config_obj.model_track == "upgrade" and not config_obj.model_upgrade_name:
        raise ValueError("Config.model_upgrade_name is required when Config.model_track='upgrade'.")

    if config_obj.rag.retrieval_mode not in {"hybrid", "vector"}:
        raise ValueError("Config.rag.retrieval_mode must be 'hybrid' or 'vector'.")


def build_runtime_config() -> config.Config:
    config_obj = config.Config()
    validate_runtime_config(config_obj)
    return config_obj


def apply_compare_policy(run_mode: str, requested_budget: int) -> int:
    if run_mode != "compare":
        return requested_budget
    return min(requested_budget, COMPARE_MAX_SAMPLE_NUMS)


def run_experiment(
        runtime_config: config.Config | None = None,
        dataset_path: str | None = None,
        max_sample_nums: int | None = None,
        log_dir: str | None = None,
) -> None:
    config_obj = runtime_config or build_runtime_config()
    validate_runtime_config(config_obj)

    effective_dataset_path = dataset_path or RUNTIME_DEFAULTS.dataset_path
    effective_log_dir = log_dir or RUNTIME_DEFAULTS.log_dir
    requested_budget = max_sample_nums or RUNTIME_DEFAULTS.max_sample_nums
    effective_budget = apply_compare_policy(
        run_mode=config_obj.run_mode,
        requested_budget=requested_budget,
    )
    if config_obj.run_mode == "compare" and requested_budget > effective_budget:
        print(
            "COMPARE_POLICY: max_sample_nums capped "
            f"from {requested_budget} to {effective_budget} in compare mode."
        )

    cvrp_dataset = load_cvrp_dataset(effective_dataset_path)
    class_config = config.ClassConfig(llm_class=sampler_lib.LLM, sandbox_class=Sandbox)

    funsearch.main(
        specification=specification,
        inputs=cvrp_dataset,
        config=config_obj,
        max_sample_nums=effective_budget,
        class_config=class_config,
        log_dir=effective_log_dir,
        dataset_path=effective_dataset_path,
    )


def main() -> None:
    run_experiment()


if __name__ == '__main__':
    main()
