from typing import Optional

import pandas as pd

from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger
from premsql.agents.base import ChartPlotWorkerBase, ChartPlotWorkerOutput
from premsql.agents.baseline.prompts import BASELINE_CHART_WORKER_PROMPT_TEMPLATE
from premsql.agents.tools.plot.base import BasePlotTool
from premsql.agents.utils import convert_df_to_dict
from premsql.security import ensure_expected_keys_only, parse_structured_output

logger = setup_console_logger("[PLOT-WORKER]")


class BaseLinePlotWorker(ChartPlotWorkerBase):
    def __init__(
        self, generator: Text2SQLGeneratorBase, plot_tool: BasePlotTool
    ) -> None:
        self.generator, self.plot_tool = generator, plot_tool

    def run(
        self,
        question: str,
        input_dataframe: pd.DataFrame,
        temperature: Optional[float] = 0.1,
        max_new_tokens: Optional[int] = 100,
        plot_image: Optional[bool] = True,
        prompt_template: Optional[str] = BASELINE_CHART_WORKER_PROMPT_TEMPLATE,
        **kwargs,
    ) -> ChartPlotWorkerOutput:
        prompt = prompt_template.format(
            columns=list(input_dataframe.columns), question=question
        )
        try:
            logger.info("Going for generation")
            to_plot = self.generator.generate(
                data_blob={"prompt": prompt},
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                postprocess=False,
            )
            plot_config = ensure_expected_keys_only(
                parse_structured_output(
                    to_plot, expected_keys={"x", "y", "plot_type"}
                ),
                expected_keys={"x", "y", "plot_type"},
            )
            fig = self.plot_tool.run(data=input_dataframe, plot_config=plot_config)
            logger.info(f"Plot config: {plot_config}")

            if plot_image:
                output = self.plot_tool.convert_image_to_base64(
                    self.plot_tool.convert_plot_to_image(fig=fig)
                )
                logger.info("Plot image generated successfully")
            else:
                output = None

            return ChartPlotWorkerOutput(
                question=question,
                input_dataframe=convert_df_to_dict(input_dataframe),
                plot_config=plot_config,
                plot_reasoning=None,
                output_dataframe=None,
                image_plot=output,
                error_from_model=None,
                additional_input={
                    "temperature": temperature,
                    "max_new_tokens": max_new_tokens,
                    **kwargs,
                },
            )

        except Exception as e:
            error_message = f"Error during plot generation: {str(e)}"
            logger.error(error_message)
            return ChartPlotWorkerOutput(
                question=question,
                input_dataframe=convert_df_to_dict(input_dataframe),
                plot_config=None,
                image_plot=None,
                plot_reasoning=None,
                error_from_model=error_message,
                additional_input={
                    "temperature": temperature,
                    "max_new_tokens": max_new_tokens,
                    **kwargs,
                },
            )
